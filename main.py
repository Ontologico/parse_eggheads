import argparse

from egg_lib import start_parsing

if __name__ == "__main__":
    """Example: nohup python -u wb2.py "inn_first.json" "inn_result.json" > log1.txt 2>&1 &"""
    parser = argparse.ArgumentParser()
    parser.add_argument("save_path", type=str, help="Путь до файла для сохранения")
    parser.add_argument("source_path", type=str, help="Путь до исходных данных")
    parser.add_argument("start_with", type=int, help="С какой строки в датасете начать парсить")
    parser.add_argument("--reverse_flag", action="store_true", help="Сортировка")

    args = parser.parse_args()

    print("start parsing...")
    start_parsing(args.save_path, args.source_path, args.reverse_flag, args.start_with)
    print("end parsing...")
