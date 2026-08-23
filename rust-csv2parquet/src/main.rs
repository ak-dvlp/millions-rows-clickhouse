use polars::prelude::*;
use std::error::Error;
use std::fs;
use std::path::Path;

/// Максимальный размер одного Parquet-файла (45 МиБ)
const MAX_FILE_SIZE_BYTES: u64 = 45 * 1024 * 1024;
/// Размер выборки для оценки размера строки (10k строк)
const SAMPLE_SIZE: usize = 10_000;

fn main() {
    let csv_dir = "../data/csv";
    let parquet_dir = "../data/parquet";

    println!("Запуск процесса конвертации...");

    if let Err(e) = process_files(csv_dir, parquet_dir) {
        eprintln!("Критическая ошибка при конвертации: {}", e);
        std::process::exit(1);
    }

    println!("Все файлы успешно конвертированы!");
}

/// Обходит CSV-директории и конвертирует CSV-файлы в Parquet-файлы с разбивкой по 45 МиБ
fn process_files(csv_dir: &str, parquet_dir: &str) -> Result<(), Box<dyn Error>> {
    fs::create_dir_all(parquet_dir)?;

    for entry in fs::read_dir(csv_dir)? {
        let entry = entry?;
        let csv_path = entry.path();

        if csv_path.is_file() && csv_path.extension().map_or(false, |ext| ext == "csv") {
            let file_stem = csv_path
                .file_stem()
                .and_then(|s| s.to_str())
                .ok_or_else(|| format!("Не удалось получить имя файла: {:?}", csv_path))?;

            println!("\nОбработка: {:?}", csv_path);

            // Чтение CSV в DataFrame
            let df = LazyCsvReader::new(csv_path.to_str().ok_or("Невалидный путь к файлу")?.into())
                .with_has_header(true)
                .with_separator(b';')
                .with_try_parse_dates(true)
                .finish()?
                .collect()?;

            let total_rows = df.height();
            if total_rows == 0 {
                println!("  Пропущено: 0 строк");
                continue;
            }

            // Определение оптимального размера блока на основе оценки количества строк
            let rows_per_block = estimate_rows_per_block(&df, MAX_FILE_SIZE_BYTES);
            println!("  Оценочный размер: ~{} строк на блок", rows_per_block);

            // Разбивка DataFrame на блоки и запись по отдельности
            let mut block_index = 1usize;
            let mut offset = 0usize;

            while offset < total_rows {
                let end = std::cmp::min(offset + rows_per_block, total_rows);
                let num_rows = end - offset;
                let block = df.slice(offset as i64, num_rows);

                let block_filename = format!("{}_part{}.parquet", file_stem, block_index);
                let parquet_path = Path::new(parquet_dir).join(&block_filename);

                // Запись блока в файл
                let file = fs::File::create(&parquet_path)?;
                let mut df_clone = block.clone();
                let writer = polars::io::parquet::write::ParquetWriter::new(file);
                writer.finish(&mut df_clone)?;

                // Отображение размера созданного файла
                let file_size = fs::metadata(&parquet_path)?.len();
                let size_mb = file_size as f64 / (1024.0 * 1024.0);
                println!(
                    "  Блок {}: {:?} | {} строк | {:.2} МиБ",
                    block_index, parquet_path, num_rows, size_mb
                );

                block_index += 1;
                offset = end;
            }

            println!("  Итого: {} файлов для {}", block_index - 1, file_stem);
        }
    }

    Ok(())
}

/// Оценивает количество строк, которое помещается в заданный размер файла.
fn estimate_rows_per_block(df: &DataFrame, max_file_size: u64) -> usize {
    let total_rows = df.height();
    if total_rows == 0 {
        return 0;
    }

    // Формирование выборки
    let sample_rows = std::cmp::min(SAMPLE_SIZE, total_rows);
    let sample = df.head(Some(sample_rows));

    // Создание временного файла в системной temp-директории
    let temp_filename = format!(
        "polars_block_estimate_{}.parquet",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs()
    );
    let temp_path = std::env::temp_dir().join(temp_filename);

    // Запись выборки во временный файл
    let file = match fs::File::create(&temp_path) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("  Не удалось создать temp-файл: {e}");
            return 50_000;
        }
    };

    let mut sample_clone = sample.clone();
    let writer = polars::io::parquet::write::ParquetWriter::new(file);
    let sample_size = match writer.finish(&mut sample_clone) {
        Ok(s) => s,
        Err(_) => {
            let _ = fs::remove_file(&temp_path);
            return 50_000;
        }
    };

    let _ = fs::remove_file(&temp_path);

    if sample_size == 0 {
        return total_rows;
    }

    // Пропорциональный расчёт
    let estimated = (max_file_size as u64 * sample_rows as u64) / sample_size;

    // Ограничение: не менее 1 строки, не более всего файла
    std::cmp::max(1, estimated as usize).min(total_rows)
}
