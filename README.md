### Создание и активация conda-окружения

```bash
conda create -n eggheads python=3.12
source activete eggheads
```

### Установка mozilla/geckodriver и firefox

```bash
conda install geckodriver
conda install conda-forge::firefox
```
### Запуск кода

```bash
nohup python -u main.py "data/" "data/sellers_ogrn.csv" 0 > log1.txt 2>&1 &
```

[1] 788366