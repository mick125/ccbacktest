# Backtest na krypto
## Adresáře
`./data_crypto` - zde je doporučeno ukládat historická data do adresáře, data nejsou součástí tohoto repa

`./runners` - soubory v tomto adresáři spouští jednotlivé simulace

## Data
`data_downloader.py` - stahuje historická data z CoinBase

`concat_data.py` - spojuje stažená historická data do jednoho souboru .parguet

## Simulace
`simulators.py` - obsahuje simulační backtest funkce

`utils.py` - pomocníčci, načítání dat z .parquet souboru

`Wallet.py` - třída peněženky, umí nakupovat a prodávat


