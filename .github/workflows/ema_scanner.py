"""
EMA Crossover Buy Signal Scanner
Based on Trader XO Macro Trend Scanner (Pine Script) logic

Scans hardcoded tickers from:
  - Finviz Midcap (2,077 tickers from uploaded CSV)
  - STOXX Europe 600 (major constituents)

Buy Signal = EMA(12) crosses above EMA(25) on the latest bar

Requirements:
    pip install yfinance pandas
"""

import yfinance as yf
import pandas as pd
import requests
import argparse
import time
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
FAST_EMA = 12
SLOW_EMA = 25
INTERVAL = "4h"   # "4h" | "1h" | "1d"
#   Note: yfinance has no native 4h — script downloads 1h and resamples.
PERIOD   = "60d"  # "60d" for intraday | "6mo" for daily

# ── TELEGRAM CONFIG ───────────────────────────────────────────────────────────
# 1. Message @BotFather on Telegram → send /token → select @StocklistEMA_bot
# 2. BotFather gives a token like:  123456789:ABCdefGHIjklMNOpqrSTUvwxyz
# 3. Start a chat with @StocklistEMA_bot (send it any message first)
# 4. Get your chat_id — visit this URL in a browser (replace <TOKEN>):
#    https://api.telegram.org/bot<TOKEN>/getUpdates
#    Find  "chat":{"id": 123456789}  in the response
# Tokens can be set here OR as environment variables on PythonAnywhere
# (Environment variables are safer — they're not stored in your code file)
import os as _os
TELEGRAM_TOKEN   = _os.environ.get("TELEGRAM_TOKEN",   "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = _os.environ.get("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")
TELEGRAM_ENABLED = TELEGRAM_TOKEN != "YOUR_BOT_TOKEN"
# ──────────────────────────────────────────────────────────────────────────────

# ── TICKER LISTS ──────────────────────────────────────────────────────────────

FINVIZ_MIDCAP = [
    "NVDA", "GOOGL", "GOOG", "AAPL", "MSFT", "AMZN", "TSM", "AVGO", "TSLA", "META",
    "BRK-B", "BRK-A", "MU", "LLY", "WMT", "JPM", "AMD", "ASML", "XOM", "INTC",
    "V", "ORCL", "JNJ", "CSCO", "COST", "MA", "CAT", "LRCX", "ABBV", "BAC",
    "NFLX", "CVX", "AMAT", "KO", "UNH", "ARM", "PG", "GE", "PLTR", "HSBC",
    "MS", "BABA", "HD", "MRK", "TXN", "GS", "AZN", "GEV", "PM", "NVS",
    "RY", "KLAC", "QCOM", "TM", "RTX", "LIN", "WFC", "SHEL", "IBM", "SNDK",
    "BHP", "MUFG", "C", "AXP", "PANW", "TMUS", "ADI", "SAP", "VZ", "TTE",
    "PEP", "DELL", "ANET", "MCD", "TD", "STX", "SAN", "NEE", "MRVL", "AMGN",
    "WDC", "DIS", "TJX", "BLK", "T", "APP", "BA", "APH", "CRWD", "GLW",
    "TMO", "GILD", "UNP", "SCCO", "ETN", "SCHW", "ISRG", "WELL", "ABT", "NVO",
    "PFE", "HON", "CRM", "SMFG", "UBS", "BX", "DE", "UBER", "BUD", "COP",
    "BTI", "PDD", "PLD", "SHOP", "RIO", "SONY", "BBVA", "HDB", "BKNG", "CB",
    "ENB", "VRT", "UL", "LMT", "DHR", "SPGI", "MO", "SYK", "NEM", "LOW",
    "BMY", "PGR", "COF", "CVS", "SBUX", "BMO", "PWR", "VRTX", "MFG", "BP",
    "PH", "SPOT", "CEG", "ACN", "CM", "EQIX", "SO", "SNY", "CDNS", "HWM",
    "NOW", "BN", "GSK", "SNPS", "CME", "TT", "SBS", "MDT", "BNS", "MAR",
    "FTNT", "CNQ", "DUK", "ADBE", "BNY", "EQNR", "FDX", "IBN", "WMB", "GD",
    "FCX", "CMI", "NOK", "MCK", "AEM", "ING", "CMCSA", "PNC", "ADP", "NGG",
    "HCA", "SLB", "UPS", "CSX", "WM", "AMT", "BE", "USB", "BSX", "JCI",
    "MNST", "ASX", "KKR", "ICE", "CIEN", "ELV", "NXPI", "MELI", "INTU", "BCS",
    "EPD", "RKLB", "MPWR", "MMM", "ABNB", "LYG", "DDOG", "AMX", "CP", "NOC",
    "EMR", "MCO", "NTES", "MDLZ", "BAM", "MRSH", "SU", "CVNA", "NET", "SHW",
    "E", "ROST", "APO", "COHR", "ORLY", "CI", "HLT", "KMI", "EOG", "MPC",
    "TRP", "PBR", "ITW", "GM", "NSC", "CL", "RCL", "VLO", "ECL", "AEP",
    "CNI", "LITE", "B", "VALE", "PSX", "TDG", "CTAS", "CRH", "AON", "MSI",
    "DLR", "WBD", "ET", "SPG", "DASH", "HOOD", "NKE", "REGN", "FIX", "BKR",
    "TRV", "MFC", "APD", "NWG", "RSG", "NU", "DB", "STM", "IMO", "SNOW",
    "F", "KEYS", "TER", "TEL", "TFC", "URI", "SRE", "AFL", "D", "WPM",
    "GWW", "PCAR", "LHX", "O", "RACE", "RELX", "TRGP", "CRWV", "MPLX", "OXY",
    "OKE", "TGT", "MSTR", "STRC", "VST", "FANG", "ALL", "NUE", "ALAB", "CVE",
    "CARR", "MET", "PSA", "MCHP", "CBRS", "UMC", "CTVA", "COR", "AME", "FLEX",
    "AJG", "NBIS", "MT", "DAL", "DVN", "NDAQ", "ETR", "EBAY", "AZO", "FAST",
    "ABEV", "ROK", "HPE", "SE", "EA", "XEL", "EW", "ADSK", "TAK", "GFS",
    "ARGX", "FER", "ON", "AU", "LNG", "INFY", "MDLN", "COIN", "DEO", "CCJ",
    "EXC", "PBR-A", "CAH", "ASTS", "GRMN", "FITB", "ODFL", "WAB", "FNV", "FERG",
    "IX", "VTR", "IDXX", "STT", "ITUB", "MSCI", "CLS", "YUM", "ERIC", "CMG",
    "CCEP", "ARES", "DHI", "WDS", "XYZ", "TTWO", "AMP", "AIG", "HLN", "CRDO",
    "BDX", "SLF", "TEVA", "KDP", "JBL", "PEG", "ESLT", "KR", "RKT", "ED",
    "CCI", "ALNY", "VIK", "WCN", "PYPL", "HSY", "LYV", "PUK", "EME", "IRM",
    "CBRE", "ADM", "KB", "HIG", "CBOE", "TRI", "CCL", "IBKR", "GFI", "UI",
    "WEC", "JD", "HEI-A", "HEI", "HUM", "PCG", "STLD", "SYY", "TKO", "SATS",
    "PRU", "BIDU", "KGC", "EQT", "VMC", "Q", "QSR", "UAL", "HAL", "HMC",
    "VOD", "PAYX", "MLM", "NTR", "CHT", "ZTS", "KVUE", "ACGL", "WAT", "ALC",
    "LVS", "RBLX", "RVMD", "KMB", "HBAN", "A", "SUNB", "ROP", "TSEM", "VG",
    "CPRT", "TECK", "SYM", "EXR", "TS", "MTB", "NTRS", "RYAAY", "EL", "MTSI",
    "AXON", "RPRX", "ONC", "MTZ", "AEE", "WDAY", "VICI", "EC", "SHG", "TCOM",
    "RMD", "DTE", "CASY", "ZS", "ATO", "FISV", "RJF", "NRG", "CQP", "ZM",
    "P", "FICO", "GEHC", "TDY", "FSLR", "DOV", "TWLO", "NTRA", "FTS", "BIIB",
    "FTI", "AMRZ", "TPR", "IR", "KHC", "CNC", "CNP", "PBA", "BAP", "VRSN",
    "OTIS", "RDDT", "DXCM", "CPNG", "CW", "TPL", "NTAP", "EIX", "NVT", "PPL",
    "IQV", "FE", "CFG", "EXPE", "XYL", "ES", "FTAI", "CRCL", "VEEV", "CINF",
    "FOXA", "FOX", "AVB", "PHG", "ROL", "DOW", "STZ", "HUBB", "JBHT", "WRB",
    "EQR", "XPO", "MDB", "FMX", "UTHR", "CTSH", "PPG", "FN", "WTW", "AWK",
    "SYF", "TW", "RF", "STRL", "IONQ", "KEY", "INSM", "NMR", "AER", "WSM",
    "PAAS", "DRI", "BNTX", "BG", "MKL", "AFRM", "BCE", "RL", "ATI", "IHG",
    "CMS", "NI", "CHD", "CPAY", "PKX", "DG", "FCNCA", "FWONK", "FWONA", "EXE",
    "PFG", "LPLA", "STLA", "MKSI", "CRS", "VRSK", "ULTA", "TSN", "L", "PHM",
    "FFIV", "HPQ", "WST", "SMCI", "LYB", "MTD", "TROW", "ILMN", "LEN", "FIS",
    "ENTG", "WIT", "VIV", "TEAM", "AKAM", "WWD", "SBAC", "DGX", "ROIV", "IREN",
    "AS", "STE", "OMC", "LH", "DKNG", "VLTO", "AXIA", "EXPD", "CHRW", "DKS",
    "LUV", "ALB", "LSCC", "BURL", "SOFI", "SW", "TTMI", "BSBR", "ULS", "DD",
    "GPN", "UDR", "CHTR", "RCI", "CX", "NXT", "AA", "SITM", "TU", "RBA",
    "PKG", "PAGP", "INCY", "EVRG", "EFX", "IFF", "BCH", "BRO", "SNX", "SNA",
    "RS", "RGLD", "YPF", "LNT", "CDE", "VTRS", "ROKU", "BWXT", "BBD", "MRNA",
    "APG", "RBC", "ESS", "FTV", "CF", "DLTR", "AMKR", "MGA", "WCC", "IOT",
    "RIVN", "WMG", "AMCR", "ITT", "BIP", "USFD", "WES", "BEKE", "GIS", "TLN",
    "KSPI", "KEP", "LII", "INVH", "WY", "EWBC", "RMBS", "BR", "IP", "H",
    "AGI", "DOCN", "NVMI", "PTC", "PL", "WPC", "PAA", "KIM", "BEN", "OKTA",
    "SN", "TLK", "PR", "CG", "VNOM", "ZBH", "FLUT", "NVR", "PHYS", "ARXS",
    "GNRC", "EMA", "TXT", "LDOS", "SSNC", "NDSN", "TPG", "GMAB", "LOGI", "GH",
    "RTO", "OVV", "NLY", "HST", "OWL", "PSLV", "NBIX", "LAMR", "TSCO", "IEX",
    "MOD", "MAA", "WSO", "DECK", "YUMC", "WSE", "SUI", "WF", "MLI", "SMTC",
    "DTM", "LULU", "THC", "VICR", "FPS", "CLH", "BSAC", "BALL", "NWSA", "NWS",
    "LTM", "GEN", "JAZZ", "PNFP", "ASND", "PFGC", "GRAB", "SKM", "SGI", "CPT",
    "LECO", "REG", "ENLT", "PS", "OHI", "AAOI", "GIB", "DOC", "RBRK", "BWA",
    "RRX", "EG", "SANM", "SUN", "TIGO", "MAS", "RGA", "IESC", "CDW", "JBS",
    "CSL", "ARMK", "AUR", "J", "CHKP", "ONTO", "TRU", "GLPI", "TOST", "ARCC",
    "UNM", "LI", "SOLS", "JLL", "GPC", "ONON", "BBY", "EVR", "CSGP", "BBIO",
    "APA", "HTHT", "SOLV", "SMMT", "VIAV", "TRMB", "AEG", "RPM", "PAYP", "ALLY",
    "TOL", "FNF", "SNN", "TYL", "XPEV", "AEIS", "PEN", "APLD", "ZTO", "GFL",
    "CNH", "AIZ", "HUT", "GGG", "HII", "DY", "MKC", "IONS", "RNR", "EXEL",
    "DVA", "SWKS", "BNT", "ELS", "CRBG", "SAIA", "WULF", "JHX", "PNW", "HAS",
    "QXO", "APTV", "TFII", "DINO", "NTNX", "IVZ", "SWK", "MEDP", "NIO", "FIVE",
    "AVY", "DRS", "GL", "NYT", "COO", "MDGL", "LFUS", "AXSM", "ZBRA", "RGC",
    "XE", "TXRH", "AGNC", "OKLO", "MP", "EQH", "PNR", "KNX", "DT", "CNA",
    "HL", "WBS", "GDDY", "BF-B", "BF-A", "COKE", "ALGN", "BTSG", "U", "CLX",
    "BLD", "GWRE", "FRVO", "PSKY", "FIG", "FHN", "AAON", "AMH", "GLXY", "GMED",
    "AIT", "HRL", "SQM", "RDY", "ARW", "ELAN", "WLK", "CGNX", "JOBY", "ALLE",
    "BEP", "AFG", "HMY", "SF", "EGP", "AR", "GIL", "ARWR", "CACI", "VSAT",
    "SPXC", "CCK", "PAG", "BMNR", "SEIC", "SJM", "MOG-A", "BJ", "PINS", "RVTY",
    "GSAT", "TIMB", "PODD", "KTOS", "AHR", "FORM", "POWL", "JEF", "BXP", "SCI",
    "FMS", "WMS", "IT", "WTRG", "HBM", "ESI", "HLI", "CR", "LUMN", "PAC",
    "AES", "FRT", "TTD", "WTS", "EHC", "ERIE", "AM", "SFD", "DPZ", "FUTU",
    "EMBJ", "SUZ", "QBTS", "VMI", "BMRN", "WTFC", "UMBF", "IAG", "FCFS", "WYNN",
    "HUBS", "ENSG", "ABVX", "AG", "BAX", "OGE", "SIRI", "GTLS", "EQX", "BSY",
    "CTRE", "RIOT", "MGM", "GME", "AAL", "BPOP", "DCI", "MUSA", "PRAX", "JKHY",
    "SIMO", "TX", "OC", "R", "ORI", "MICC", "DOCU", "BAH", "BRX", "SNAP",
    "ALV", "CART", "QRVO", "CNM", "LINE", "W", "CYTK", "UHS", "ALSN", "ALGM",
    "RRC", "DAR", "FLY", "CIFR", "LGN", "FLS", "ONB", "AGX", "MASI", "CAVA",
    "SSB", "ACM", "ZION", "UHAL-B", "UHAL", "MOH", "PSO", "AVAV", "CUBE", "ADC",
    "SNEX", "AYI", "CRUS", "DDS", "SAIL", "SARO", "LLYVK", "LLYVA", "KRYS", "BVN",
    "XP", "ENS", "TTC", "LEVI", "TKR", "FROG", "BROS", "CEF", "MSGS", "ENPH",
    "KT", "STN", "FR", "CFR", "ELPC", "COLB", "PRMB", "ICLR", "CHWY", "WAL",
    "PRI", "AXTI", "MXL", "SBSW", "GAP", "ASR", "NNN", "EGO", "ORA", "FRHC",
    "SSL", "RYAN", "EMN", "ICL", "ARE", "MBLY", "HSIC", "FDS", "VFS", "MTCH",
    "CORZ", "TEM", "YOU", "RGTI", "IBRX", "NUVL", "AGCO", "MANH", "REXR", "CWEN",
    "KNTK", "ZG", "Z", "CMC", "HESM", "AMG", "HALO", "ZWS", "FRO", "OSK",
    "SFM", "VIRT", "BOKF", "AOS", "KRMN", "YMM", "EDU", "CAMT", "BIRK", "BLDR",
    "BIO", "JHG", "CIB", "NE", "IDA", "ESE", "NCLH", "SOBO", "WFRD", "SSD",
    "ACI", "TAP", "FIGR", "CHRD", "ECG", "KEX", "PDI", "UGI", "CAE", "CBSH",
    "SM", "VLY", "NFG", "CELH", "NOV", "LUNR", "CRL", "TECH", "VOYA", "KGS",
    "NVTS", "ATR", "JXN", "LTH", "STAG", "ST", "QGEN", "CDP", "HQY", "AVT",
    "PLXS", "AXS", "CWAN", "NXE", "PCVX", "RIG", "MYRG", "RHP", "SLAB", "TTEK",
    "KNSL", "MOS", "LEA", "PCOR", "VCX", "BRKR", "HR", "FSS", "TRNO", "VIST",
    "PB", "BEPC", "JBTM", "PRIM", "NEU", "BBUC", "RAL", "IMVT", "FAF", "LKQ",
    "CBC", "OR", "OGC", "LSTR", "VSH", "THG", "LNC", "CLF", "GDS", "AWI",
    "MIDD", "IDCC", "EPRT", "TEX", "MORN", "GKOS", "NPO", "CHYM", "PPC", "VNO",
    "MSA", "DOX", "MTDR", "VAL", "POOL", "KYMR", "HXL", "UEC", "CENX", "OSCR",
    "TXNM", "SGHC", "AROC", "CELC", "VFC", "FLR", "TFPM", "LNTH", "INGR", "ROAD",
    "RGEN", "CORT", "URBN", "SWX", "LAD", "STWD", "GTES", "PTGX", "AXTA", "AN",
    "SSRM", "KLAR", "SYRE", "EXP", "GTX", "S", "AUGO", "MHK", "PAYC", "GBCI",
    "BTG", "CAG", "COMP", "FNB", "STEP", "APGE", "INGM", "ALKS", "OMF", "MDA",
    "RYN", "USAR", "SRRK", "ACA", "RYTM", "CNTA", "FSV", "PACS", "MAC", "ETSY",
    "GATX", "RSI", "GGAL", "TGTX", "MSM", "DSGX", "SNDR", "WH", "MIRM", "UBSI",
    "PSN", "VSNT", "CPB", "BYD", "ACT", "BILI", "EAT", "TTAN", "RRR", "MRCY",
    "DBX", "VIPS", "UGP", "ENIC", "LOAR", "CAR", "OUT", "PCTY", "CPA", "IBP",
    "FLG", "GVA", "TFX", "GGB", "LW", "NOVT", "NJR", "CHE", "COGT", "APPF",
    "ZGN", "CHDN", "CZR", "CACC", "IFS", "PATH", "POR", "ABCB", "CROX", "KMX",
    "ESAB", "PIPR", "CE", "NXST", "PEGA", "NSA", "ACMR", "M", "KOF", "SYNA",
    "BLTE", "LB", "BKH", "KLIC", "OTEX", "PECO", "ESTC", "BLCO", "MCY", "PTCT",
    "AMTM", "BIPC", "MATX", "KRG", "ESNT", "AVTR", "OBDC", "ALM", "SEI", "CWST",
    "HWC", "HIMS", "GXO", "BXSL", "MTG", "NICE", "TME", "VCTR", "OZK", "LEGN",
    "TMHC", "ADT", "AUB", "CGON", "EQPT", "MARA", "CRC", "BC", "LPL", "HOMB",
    "MC", "RUSHA", "MGY", "QS", "PLUG", "BZ", "SIGI", "DLB", "LQDA", "XNDU",
    "IRDM", "G", "WTM", "GOLF", "HASI", "GLNG", "APLS", "SBRA", "MUR", "FND",
    "XENE", "LBRT", "BLSH", "EPAM", "BCPC", "RITM", "CHH", "PSMT", "BGC", "LYFT",
    "LPX", "WEX", "OGS", "PRM", "SR", "GNTX", "IPGP", "IEP", "ACLS", "SITE",
    "HLNE", "JAN", "WHD", "GLBE", "BMA", "WFG", "AX", "BOOT", "SIM", "UWMC",
    "CRSP", "SXT", "DIOD", "DUOL", "ALH", "TKC", "ACHR", "MAAS", "BB", "GBTG",
    "OTF", "HRB", "HCC", "SON", "OLLI", "CNX", "STVN", "CIGI", "ZETA", "VSEC",
    "ALK", "XMTR", "PI", "NTSK", "ONDS", "LBRDK", "LBRDA", "NAVN", "LAZ", "GHC",
    "RLI", "CSTM", "SPHR", "AQN", "CMBT", "MAIN", "RDN", "NNNN", "DNTH", "LGND",
    "SEB", "ASB", "LAUR", "POWI", "FFIN", "XXI", "EBC", "MIAX", "WSC", "MKTX",
    "KEN", "MDU", "NNI", "MEOH", "MTRN", "INDV", "CSW", "FCN", "UFPI", "LASR",
    "PTEN", "UUUU", "REYN", "UNF", "FBIN", "MWH", "SHC", "IBOC", "HRI", "REZI",
    "PBF", "EPR", "GTLB", "MTN", "MIR", "TAL", "TFSL", "AIR", "PFSI", "SMR",
    "CVLT", "NWE", "FELE", "CNR", "VSCO", "EXLS", "PAM", "CUZ", "BCO", "LMND",
    "CLSK", "CNO", "CAI", "RDW", "TCBI", "FTDR", "AD", "MAT", "CBT", "SAIC",
    "COCO", "OLED", "PVH", "ORLA", "POST", "VVV", "KVYO", "OPEN", "MTH", "ACIW",
    "YSS", "SEDG", "ANDG", "OMAB", "RELY", "MANE", "SFBS", "LION", "MRP", "RDNT",
    "KBR", "BDC", "KNF", "FHI", "COLD", "CVSA", "AZZ", "EMAT", "NAMS", "USAC",
    "TREX", "TAC", "PLNT", "CIG", "CAAP", "DOO", "TNL", "SLM", "FULT", "STNG",
    "VNT", "LIVN", "BRC", "TDS", "SKT", "RXO", "TVTX", "THO", "CRGY", "AMBA",
    "DNP", "EE", "LOPE", "HNGE", "FRMI", "ATMU", "INSW", "LBTYK", "LBTYA", "AMRX",
    "KNSA", "CVCO", "TBBB", "HAFN", "SRAD", "KRC", "PHI", "PSUS", "TWST", "MWA",
    "HP", "UCB", "IRT", "SLGN", "MMYT", "NP", "WPP", "TPH", "HGV", "SKY",
    "GFF", "ENVA", "MNSO", "BNL", "KTB", "PJT", "FLNC", "MNDY", "TPC", "GPI",
    "UCTT", "UTG", "TDW", "PII", "VEON", "MRX", "CATY", "OII", "KAI", "KC",
    "BETA", "BLLN", "RUM", "BELFB", "BELFA", "CRNX", "CRK", "INDB", "MMSI", "CPRX",
    "WING", "NVST", "RNST", "VECO", "DAN", "LRN", "HHH", "OPLN", "WSFS", "FBP",
    "WAY", "BANF", "IRTC", "ITRI", "HIMX", "ATAT", "BMI", "OTTR", "SEZL", "ARX",
    "NHI", "FG", "JOE", "CNS", "BTDR", "CVBF", "STUB", "GPGI", "OSIS", "NG",
    "ARIS", "ACAD", "SKE", "BTE", "EWTX", "LEU", "QLYS", "CALM", "BHF", "DORM",
    "BFH", "ERAS", "VKTX", "BBWI", "DOCS", "RNG", "VRNS", "ORKA", "HGTY", "WOLF",
    "SUNC", "BOX", "ABG", "EXTR", "KFY", "VCYT", "OGN", "AB", "SOUN", "ASO",
    "FIBK", "APLE", "RUN", "YETI", "CGAU", "BILL", "INFQ", "DLO", "GNW", "AEHR",
    "AAUC", "SKYW", "BKU", "AVA", "SMG", "BFAM", "GBDC", "CBU", "NEA", "ATS",
    "BBAR", "MANU", "SLG", "FOUR", "MHO", "SA", "AGO", "ICUI", "COLM", "ANF",
    "WSBC", "PTRN", "OPCH", "KYIV", "MSGE", "FIZZ", "FHB", "SIG", "NATL", "MCHB",
    "BULL", "PPTA", "AAP", "CC", "ALHC", "LIF", "GEF", "SII", "FUL", "EFXT",
    "BWLP", "AVEX", "PONY", "CSQ", "CSAN", "KN", "HWKN", "FFBC", "CON", "SXI",
    "TLX", "AVNT", "CECO", "BKD", "ARLP", "ELF", "CLBT", "CAKE", "PLAB", "MMS",
    "BHE", "CNK", "TOWN", "CVI", "DAVE", "BATRA", "BATRK", "CTRI", "IAC", "BTU",
    "TRMD", "HG", "NN", "MMED", "USLM", "TDC", "SBLK", "SFNC", "CHEF", "MZTI",
    "INOD", "WRBY", "ETOR", "TXG", "SHOO", "ADEA", "VC", "LXP", "BOH", "SDRL",
    "KEEL", "GPOR", "CRVL", "PRK", "ADX", "KBH", "BXMT", "DNLI", "APAM", "BEAM",
    "NIC", "ITGR", "VTMX", "HAWK", "CPK", "WIX", "GPK", "ZIM", "HAE", "PATK",
    "CURB", "HYMC", "PLMR", "RCUS", "AKR", "HAYW", "FSK", "KALU", "GEO", "DNN",
    "UTF", "UNFI", "NSIT", "MPT", "ATRO", "UE", "NTCT", "ERO", "DYN", "CWK",
    "AWR", "SBCF", "FSM", "OLN", "IPAR", "NHC", "EOSE", "BKV", "CLMT", "GRAL",
    "BANC", "BGSI", "DBRG", "WT", "HTGC", "LFST", "UPST", "JPC", "PAY", "PFS",
    "TE", "BSM", "VGNT", "TTAM", "TNGX", "HIW", "GRBK", "EXG", "ATKR", "ARCB",
    "AEO", "MGEE", "TR", "VISN", "TENB", "ALMS", "PHIN", "BRZE", "QTWO", "EXK",
    "PARR", "NMIH", "KMT", "GPCR", "IHS", "DHT", "PRVA", "DX", "KLRA", "EXPO",
    "CALY", "INTR", "PENG", "HSAI", "FCPT", "SUPN", "WK", "WHR", "SLNO", "RHI",
    "FBK", "FSLY", "WDFC", "VOYG", "SVM", "DBD", "STNE", "MGRC", "NAD", "WOR",
    "VAC", "UNIT", "DKL", "WTTR", "OUST", "SPNT", "HLIO", "RLAY", "LCII", "KD",
    "CCC", "BWIN", "PLBL", "AAMI", "AYA", "BW", "VNET", "WAFD", "NVG", "ASH",
    "CDLR", "SHAK", "ARQT", "QUBT", "TARS", "TRMK", "FA", "DK", "RH", "TNK",
    "HUBG", "NESR", "CUBI", "CWT", "IRON", "FRSH", "ELVN", "NYAX", "HUN", "FRME",
    "GDV", "TGB", "DGII", "IDYA", "WU", "NMRK", "BRAI", "CALX", "IVT", "ROG",
    "EEFT", "TRN", "PAGS", "KWR", "GMRS", "AMSC", "ICHR", "AMPX", "BKE", "CMPR",
    "CARG", "FRPT", "PTY", "PTON", "DFTX", "SAH", "IMNM", "MLYS", "TALO", "OSW",
    "VERA", "NIQ", "FBNC", "BBT", "AMR", "HTFL", "WERN", "GRDN", "HOG", "TMC",
    "AMBP", "TMDX", "ANDE", "NBTB", "MTX", "CLDX", "FLOC", "PK", "AESI", "HTO",
    "NZF", "DNOW", "AERO", "LCLN", "BCC", "UAA", "UA", "NGVT", "VVX", "ETY",
    "KYN", "NOG", "HE", "DAC", "COHU", "DRD", "CXT", "THR", "ALGT", "ABM",
    "MCW", "AKO-B", "GOF", "MH", "TBBK", "BUSE", "LCID", "WRD", "MNR", "PLUS",
    "DJT", "DXPE", "PENN", "RVT", "XIFR", "RARE", "GRND", "CSGS", "PBH", "DRH",
    "NTB", "DCO", "RAMP", "ADPT", "DRVN", "CLM", "HNI", "LMAT", "KOD", "CDNL",
    "EFSC", "AGYS", "IMAX", "BANR", "PCT", "NEXT", "CYD", "NKTR", "CENTA", "CENT",
    "HTH", "CPRI", "AXGN", "CTOS", "NGL", "UTI", "GCMG", "AVPT", "BLBD", "RNW",
    "JOYY", "CCU", "ALRM", "CEPU", "WLY", "ACHC", "BCRX", "MBIN", "MLCO", "SYBT",
    "FIGS", "ESTA", "DHC", "SLDE", "EZPW", "ATEN", "PRDO", "SOC", "CLBK", "NVCR",
    "VERX", "NMM", "PBI", "NWN", "ARR", "WS", "CXW", "MCRI", "BRSL", "ZLAB",
    "PHVS", "STC", "PUMP", "GRFS", "NWBI", "IE", "INVX", "FUN", "ECO", "HCM",
    "SEM", "TRVI", "POET", "TGS", "FORTY", "PSNY", "SHO", "BSTZ", "GTY", "IOSP",
    "BHC", "GNL", "EVT", "HCI", "OMCL", "BBAI", "XRAY"]

STOXX600 = [
    # ── United Kingdom (.L) ────────────────────────────────────────────────
    "AZN.L",  "SHEL.L", "HSBA.L", "BP.L",   "ULVR.L", "GSK.L",  "RIO.L",
    "VOD.L",  "BARC.L", "LLOY.L", "NWG.L",  "STAN.L", "BATS.L", "IMB.L",
    "DGE.L",  "NG.L",   "SSE.L",  "SVT.L",  "UU.L",   "WPP.L",  "REL.L",
    "PSON.L", "AUTO.L", "OCDO.L", "TSCO.L", "SBRY.L", "MKS.L",  "NXT.L",
    "JD.L",   "ABF.L",  "BTRW.L", "PSN.L",  "TW.L",   "BKG.L",  "CRDA.L",
    "RR.L",   "BA.L",  "WEIR.L", "IMI.L",  "MNDI.L", "EXPN.L", "SGRO.L",
    "LAND.L", "BLND.L", "CNA.L",  "LSEG.L", "III.L",  "SMWH.L", "ITV.L",
    "SKG.L",  "CRH.L",  "HLMA.L", "DCC.L",  "ITRK.L", "DPLM.L",
    # ── Germany (.DE) ──────────────────────────────────────────────────────
    "SAP.DE",  "SIE.DE",  "ALV.DE",  "MRK.DE",  "BAYN.DE", "BMW.DE",
    "VOW3.DE", "MBG.DE",  "DTE.DE",  "DB1.DE",  "BAS.DE",  "EOAN.DE",
    "RWE.DE",  "HEN3.DE", "MUV2.DE", "ADS.DE",  "ZAL.DE",  "IFX.DE",
    "FRE.DE",  "MTX.DE",  "CON.DE",  "DHER.DE", "SY1.DE",  "HFG.DE",
    "PAH3.DE", "ENR.DE",  "AFX.DE",  "DHL.DE",  "PUM.DE",  "VNA.DE",
    "LEG.DE",  "AIR.DE",
    # ── France (.PA) ───────────────────────────────────────────────────────
    "MC.PA",   "OR.PA",   "TTE.PA",  "SAN.PA",  "BNP.PA",  "ACA.PA",
    "GLE.PA",  "AIR.PA",  "AI.PA",   "SU.PA",   "VIE.PA",  "VIV.PA",
    "ORA.PA",  "KER.PA",  "RMS.PA",  "SGO.PA",  "CAP.PA",  "CS.PA",
    "LR.PA",   "RI.PA",   "ATO.PA",  "DG.PA",   "ML.PA",   "EN.PA",
    "HO.PA",   "SW.PA",   "URW.PA",  "WLN.PA",  "BIM.PA",  "ERF.PA",
    # ── Switzerland (.SW) ──────────────────────────────────────────────────
    "NESN.SW", "RO.SW",  "NOVN.SW", "ABBN.SW", "UBSG.SW",  "ZURN.SW",
    "SREN.SW", "GIVN.SW", "LONN.SW", "BAER.SW", "SCMN.SW", "TEMN.SW",
    "SIKA.SW", "GEBN.SW", "HOLN.SW", "PGHN.SW", "SLHN.SW", "CFR.SW",
    "KNIN.SW", "LISN.SW", "BARN.SW", "AMS.SW",
    # ── Netherlands (.AS) ──────────────────────────────────────────────────
    "ASML.AS", "INGA.AS", "PHIA.AS", "NN.AS",   "RAND.AS", "HEIA.AS",
    "WKL.AS",  "AD.AS",   "BESI.AS", "AKZA.AS", "MT.AS",   "IMCD.AS",
    "ABN.AS",  "LIGHT.AS",
    # ── Spain (.MC) ────────────────────────────────────────────────────────
    "IBE.MC",  "REP.MC",  "BBVA.MC", "SAN.MC",  "TEF.MC",  "ITX.MC",
    "AMS.MC",  "AENA.MC", "FER.MC",  "ACS.MC",  "CABK.MC", "SAB.MC",
    "MAP.MC",  "ELE.MC",  "RED.MC",  "GRF.MC",  "IAG.MC",  "COL.MC",
    "ENG.MC",  "MEL.MC",
    # ── Italy (.MI) ────────────────────────────────────────────────────────
    "ENI.MI",   "ENEL.MI", "ISP.MI",  "UCG.MI",  "STMPA.PA",  "TIT.MI",
    "RACE.MI",  "PRY.MI",  "LDO.MI",  "BAMI.MI", "MB.MI",   "MONC.MI",
    "AMP.MI",   "G.MI",    "SRG.MI",  "TRN.MI",  "A2A.MI",  
    "STLAM.MI",  "CPR.MI",
    # ── Sweden (.ST) ───────────────────────────────────────────────────────
    "ERIC-B.ST", "VOLV-B.ST", "SEB-A.ST",   "SHB-A.ST",   "SWED-A.ST",
    "ASSA-B.ST", "ATCO-A.ST", "INVE-B.ST",  "SAND.ST",    "SKF-B.ST",
    "TEL2-B.ST", "TELIA.ST",  "EVO.ST",     "ALIV-SDB.ST","BOL.ST",
    "ALFA.ST",   "HEXA-B.ST", "NIBE-B.ST",  "SSAB-A.ST",  "ESSITY-B.ST",
    "AXFO.ST",
    # ── Denmark (.CO) ──────────────────────────────────────────────────────
    "NOVO-B.CO", "MAERSK-B.CO", "DSV.CO",    "COLO-B.CO", "ORSTED.CO",
    "CARL-B.CO", "GN.CO",       "RBREW.CO",  "FLS.CO",   "AMBU-B.CO",
    "PNDORA.CO",    "DEMANT.CO", 
    # ── Finland (.HE) ──────────────────────────────────────────────────────
    "NOKIA.HE", "NESTE.HE", "FORTUM.HE", "SAMPO.HE", "UPM.HE",
    "STERV.HE", "KNEBV.HE", "OUT1V.HE",  "TIETO.HE",
    # ── Belgium (.BR) ──────────────────────────────────────────────────────
    "UCB.BR", "ABI.BR", "SOLB.BR", "ACKB.BR", "GLPG.BR",
    "KBC.BR", "ARGX.BR", "WDP.BR",  "GBLB.BR",  "PROX.BR",
    # ── Austria (.VI) ──────────────────────────────────────────────────────
    "OMV.VI", "VIG.VI", "RBI.VI",
    # ── Ireland (.IR) ──────────────────────────────────────────────────────
    "A5G.IR", "BIRG.IR", 
    # ── Norway (.OL) ───────────────────────────────────────────────────────
    "EQNR.OL", "DNB.OL", "TEL.OL", "MOWI.OL", "SALM.OL",
    "YAR.OL",  "ORK.OL", "AKRBP.OL","SUBC.OL",
    # ── Poland (.WA) ───────────────────────────────────────────────────────
    "PKN.WA", "PKO.WA", "PZU.WA", "LPP.WA", "KGH.WA",
    # ── Austria (new additions) ──────────
    "EBS.VI", "VER.VI", "VOE.VI", "WIE.VI",
    # ── Belgium (new additions) ──────────
    "AGS.BR", "AZE.BR", "COLR.BR", "MELE.BR", "ONTEX.BR", "UMI.BR", "BPOST.BR", "DIE.BR",
    # ── Bermuda (new additions) ──────────
    "HSX.L",
    # ── Denmark (new additions) ──────────
    "TRYG.CO", "VWS.CO", 
    # ── Finland (new additions) ──────────
    "ELISA.HE", "METSO.HE", "NDA-SE.ST", "SANOMA.HE", "VALMT.HE",
    # ── France (new additions) ──────────
    "SAF.PA", "AC.PA", "ALO.PA", "AKE.PA", "EN.PA", "BVI.PA", 
    "BN.PA", "EDEN.PA", "FGR.PA", "ENGI.PA", "ETL.PA", "FRVIA.PA", "GFC.PA",
    "GET.PA", "IPN.PA", "NEX.PA", "RNL.PA", "SCR.PA", "RCO.PA",
    "RNO.PA", "RXL.PA", "TEP.PA", "UBI.PA", "FR.PA", "VK.PA", "VCT.PA",
    "MF.PA", "AF.PA", "ATO.PA", "ENGI.PA", 
    # ── Germany (new additions) ──────────
    "AIXA.DE", "BEI.DE", "BNR.DE", "CBK.DE", "EVK.DE", "EVT.DE", "FNTN.DE",
    "FME.DE", "G1A.DE", "HNR1.DE", "HEI.DE", "BOSS.DE", "LXS.DE", "LHA.DE", 
    "NEM.DE", "PBB.DE", "P911.DE", "RHM.DE", "TKA.DE", "TUI1.DE", "FRA.DE",
    "SRT3.DE", "G24.DE", "SIX2.DE", "TLX.DE", "TMV.DE", "8TRA.DE", 
     "AT1.DE", "EVD.DE", "DTG.DE",
    # ── Greece (new additions) ──────────
    "ETE.AT",
    # ── Ireland (new additions) ──────────
    "FLTR.L", "GL9.IR", 
    # ── Israel (new additions) ──────────
    "TEVA",
    # ── Italy (new additions) ──────────
    "NEXI.MI", "REC.MI", "PIRC.MI", "PST.MI", "BC.MI", 
    
    # ── Luxembourg (new additions) ──────────
    "INPST.AS", "TEN.MI",
    # ── Netherlands (new additions) ──────────
    "STLAM.MI", "ADYEN.AS", "ASM.AS", "ENX.PA", "EXO.AS", "KPN.AS", "OCI.AS", "PNL.AS",
    "QIA.DE", "TOM2.AS", "UMG.AS", "VPK.AS", "FLOW.AS", 
    # ── Norway (new additions) ──────────
    "LSG.OL", "NHY.OL",   "TGS.OL", 
    # ── Poland (new additions) ──────────
    "CDR.WA",
    # ── Portugal (new additions) ──────────
    "JMT.LS", "EDP.LS", "EDPR.LS", "GALP.LS",
    # ── Spain (new additions) ──────────
    "BKT.MC", "NTGY.MC", "MRL.MC", "ANA.MC", "ANE.MC", "ACX.MC", "ALM.MC",
    "DIA.MC", 
    # ── Sweden (new additions) ──────────
    "HM-B.ST", "ELUX-B.ST", "BALD-B.ST", "CAST.ST", "EPI-A.ST", "HUSQ-B.ST", "INDT.ST",
     "SECU-B.ST", "SKA-B.ST", "SHB-B.ST", "SWEC-B.ST", "TREL-B.ST", "VPLAY-B.ST",
    "VITR.ST", "WIHL.ST", "CAST.ST", 
    # ── Switzerland (new additions) ──────────
    "STMN.SW", "SOON.SW", "SCHP.SW", "UHR.SW", "LOGN.SW",  "GALE.SW",
    "EMSN.SW", "ADEN.SW", "ALC.SW", "CLN.SW", "DOCM.SW", "GF.SW",
    "OERL.SW", "SGSN.SW", "SIGN.SW", "VACN.SW", "SDZ.SW",
    "SPSN.SW", "DSFIR.AS",
    # ── United Kingdom (new additions) ──────────
    "PRU.L", "HLN.L", "INF.L", "GLEN.L", "CPG.L", "RKT.L", "SPX.L", "SGE.L",
    "SMT.L", "MNG.L", "SN.L", "SMIN.L", "ENT.L",  "UTG.L", "BRBY.L",
    "NXT.L", "KGF.L", "ADM.L", "AAL.L", "ANTO.L",  "AV.L", "BME.L",
    "BA.L", "BBY.L", "BEZ.L", "BT-A.L", "BNZL.L", "CTEC.L", "DLN.L", 
    "EZJ.L", "EDV.L", "GAW.L", "HAS.L", "HIK.L", "HWDN.L", "INCH.L",
    "IHG.L", "ICG.L", "JMAT.L", "MCG.L", "MCG.L", 
    "TATE.L", "WTB.L", "PNN.L", "QLT.L", "RTO.L",
    "RMV.L", "SFOR.L", "SDR.L", "SCT.L",  "STJ.L",  "TPK.L",
    "TPK.L", "WISE.L", "AML.L", "BYG.L", "CTG.L", "GRG.L", "HTWS.L",
    "IGG.L",  "LGEN.L", "MONY.L"]

INDICES = {
    "Finviz Midcap":    FINVIZ_MIDCAP,
    "STOXX Europe 600": STOXX600,
}

# ── TRADINGVIEW URL HELPER ────────────────────────────────────────────────────
_TV_EXCHANGE = {
    ".L":  "LSE",    ".DE": "XETR",  ".PA": "EURONEXT", ".AS": "EURONEXT",
    ".SW": "SWX",    ".MI": "MIL",   ".ST": "OMX",      ".CO": "OMXC",
    ".HE": "OMXH",   ".BR": "EURONEXT", ".VI": "WBAG",  ".IR": "EURONEXT",
    ".OL": "OSL",    ".LS": "EURONEXT", ".WA": "GPW",   ".AT": "ATHEX",
    ".TA": "TASE",   ".MC": "BME",
}

def tv_url(ticker: str) -> str:
    """Return a TradingView deep link that opens the iOS app directly.
    Uses the tradingview:// URL scheme — Telegram hands this to iOS
    which launches the TradingView app instead of opening a browser.
    """
    for suffix, exchange in _TV_EXCHANGE.items():
        if ticker.upper().endswith(suffix.upper()):
            base = ticker[:-(len(suffix))].replace("-", "")
            return f"https://www.tradingview.com/chart/?symbol={exchange}:{base}"
    return f"https://www.tradingview.com/chart/?symbol={ticker}"
# ──────────────────────────────────────────────────────────────────────────────


# ── SIGNAL LOGIC ─────────────────────────────────────────────────────────────

def compute_ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def check_buy_signal(ticker: str, lookback: int = 1) -> dict | None:
    """
    Check if EMA(fast) crossed above EMA(slow) within the last `lookback` bars.
    lookback=1  → only the most recent closed bar (default)
    lookback=N  → any of the last N bars (--history mode)
    Returns the most recent signal found, or None.
    """
    try:
        fetch_interval = "1h" if INTERVAL == "4h" else INTERVAL
        # Some European stocks only have 30d of intraday data on Yahoo Finance.
        # Retry with a shorter period if the first attempt returns nothing.
        fallback_periods = [PERIOD, "30d"] if fetch_interval != "1d" else [PERIOD]
        df = None
        for _period in fallback_periods:
            _df = yf.download(ticker, period=_period, interval=fetch_interval,
                              progress=False, auto_adjust=True)
            if _df is not None and not _df.empty:
                df = _df
                break
        if df is None or df.empty:
            return None
        # yfinance 2.x returns MultiIndex columns (Price, Ticker) — flatten
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if INTERVAL == "4h":
            df = df.resample("4h", origin="epoch").agg({
                "Open": "first", "High": "max",
                "Low":  "min",   "Close": "last", "Volume": "sum"
            })
            # Drop bars with no real trading activity (overnight / pre-market
            # blocks have 0 volume and push genuine bars to wrong positions)
            df = df[df["Volume"].fillna(0) > 0].dropna(subset=["Close"])
        if len(df) < SLOW_EMA + lookback + 5:
            return None

        close = df["Close"].squeeze()
        fast  = compute_ema(close, FAST_EMA)
        slow  = compute_ema(close, SLOW_EMA)
        fmt   = "%Y-%m-%d %H:%M" if INTERVAL != "1d" else "%Y-%m-%d"

        # Scan from most-recent bar backwards
        for i in range(1, lookback + 1):
            buy_now  = fast.iloc[-i]   > slow.iloc[-i]
            buy_prev = fast.iloc[-i-1] > slow.iloc[-i-1]
            if buy_now and not buy_prev:
                bars_ago = i - 1
                return {
                    "ticker":   ticker,
                    "date":     df.index[-i].strftime(fmt),
                    "bars_ago": bars_ago,
                    "price":    round(float(close.iloc[-i]), 2),
                    "fast_ema": round(float(fast.iloc[-i]), 2),
                    "slow_ema": round(float(slow.iloc[-i]), 2),
                }
    except Exception:
        pass
    return None

# ── SCANNER ───────────────────────────────────────────────────────────────────

def scan(tickers: list[str], index_name: str, lookback: int = 1) -> list[dict]:
    signals = []
    total   = len(tickers)

    for i, ticker in enumerate(tickers, 1):
        print(f"  [{index_name}] {ticker:<12} ({i}/{total})", end="\r")
        result = check_buy_signal(ticker, lookback)
        if result:
            signals.append(result)
        if i % 60 == 0:
            time.sleep(2)

    print(" " * 60, end="\r")
    return signals

# ── OUTPUT ────────────────────────────────────────────────────────────────────

def print_results(signals: list[dict], index_name: str, lookback: int) -> None:
    width = 70
    label = f"last {lookback} bars" if lookback > 1 else "latest bar"
    print(f"\n{chr(9472) * width}")
    print(f"  {index_name}  —  {len(signals)} buy signal(s) found  [{label}]")
    print(f"{chr(9472) * width}")

    if not signals:
        print(f"  No buy signals on the {label}.\n")
        return

    signals = sorted(signals, key=lambda x: (x["bars_ago"], x["ticker"]))
    print(f"  {'Ticker':<12}  {'Date / Time':<17}  {'Bars Ago':>8}  {'Price':>10}  {'Fast EMA':>9}  {'Slow EMA':>9}")
    print(f"  {chr(9472) * 66}")
    for s in signals:
        ago = "latest" if s["bars_ago"] == 0 else f"{s['bars_ago']}b ago"
        print(f"  {s['ticker']:<12}  {s['date']:<17}  {ago:>8}  "
              f"{s['price']:>10.2f}  {s['fast_ema']:>9.2f}  {s['slow_ema']:>9.2f}")
    print()

def _esc(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    import re
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', str(text))


def format_telegram(all_signals: list[dict], lookback: int, interval: str, now: str) -> str:
    """Build one consolidated Telegram MarkdownV2 message grouped by index."""
    label = f"last {lookback} bars" if lookback > 1 else "latest bar"
    total = len(all_signals)

    if not total:
        return (
            f"*📊 EMA Scanner*  {_esc(now)}\n"
            f"Interval: *{_esc(interval)}*  \\|  Mode: {_esc(label)}\n\n"
            f"No buy signals found\\."
        )

    lines = [
        f"*📊 EMA Scanner*  {_esc(now)}",
        f"Interval: *{_esc(interval)}*  \\|  Mode: {_esc(label)}",
        f"Total signals: *{_esc(total)}*",
        "",
    ]

    # Only report signals from the most recent bar that had any signal.
    # This prevents the same tickers appearing again in the next scheduled run.
    freshest = min(s["bars_ago"] for s in all_signals)
    fresh_signals = [s for s in all_signals if s["bars_ago"] == freshest]
    ago_label = "latest bar" if freshest == 0 else f"{freshest} bar(s) ago"

    from collections import defaultdict
    by_index = defaultdict(list)
    for s in fresh_signals:
        by_index[s.get("index", "Unknown")].append(s)

    lines[2] = f"Signals from: *{_esc(ago_label)}*  \\|  Total: *{_esc(len(fresh_signals))}*"

    for index_name, signals in by_index.items():
        count = len(signals)
        lines.append(f"*{_esc(index_name)}*  \\({count} signal{'s' if count > 1 else ''}\\)")
        for s in sorted(signals, key=lambda x: x["ticker"]):
            url   = tv_url(s["ticker"])
            price = f"{s['price']:.2f}"
            lines.append(
                f"🟢 [{_esc(s['ticker'])}]({url})"
                f"  {_esc(s['date'])}"
                f"  💰 {_esc(price)}"
            )
        lines.append("")

    return "\n".join(lines).strip()

def send_telegram(text: str) -> None:
    """Send a message via Telegram bot. Silently skips if not configured."""
    if not TELEGRAM_ENABLED:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       text,
            "parse_mode": "MarkdownV2",
        }, timeout=10)
        if not resp.ok:
            print(f"  [Telegram] Error: {resp.text}")
        else:
            print("  [Telegram] Message sent ✓")
    except Exception as e:
        print(f"  [Telegram] Failed: {e}")

def export_csv(all_signals: list[dict]) -> None:
    if not all_signals:
        print("  No signals to export.\n")
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename  = f"buy_signals_{timestamp}.csv"
    pd.DataFrame(all_signals).to_csv(filename, index=False)
    print(f"  ✓ Exported {len(all_signals)} signal(s) → {filename}\n")

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EMA Crossover Buy Signal Scanner")
    parser.add_argument(
        "--history", type=int, default=1, metavar="N",
        help="Look back N bars for signals (default: 1 = latest bar only)"
    )
    parser.add_argument(
        "--interval", type=str, default=None,
        choices=["4h", "1h", "1d"],
        help="Override the chart interval (default: uses INTERVAL from config)"
    )
    parser.add_argument(
        "--period", type=str, default=None,
        help="Override the lookback period e.g. 60d, 6mo, 1y (default: from config)"
    )
    parser.add_argument(
        "--no-csv", action="store_true",
        help="Skip CSV export (useful when running in the cloud)"
    )
    args = parser.parse_args()
    lookback = max(1, args.history)

    # CLI overrides for interval / period
    if args.interval:
        INTERVAL = args.interval
    if args.period:
        PERIOD = args.period
    # Auto-adjust period when switching to daily to ensure enough bars
    if INTERVAL == "1d" and PERIOD == "60d":
        PERIOD = "6mo"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = f"latest bar" if lookback == 1 else f"last {lookback} bars"
    active_interval = INTERVAL if not args.interval else args.interval
    active_period   = PERIOD   if not args.period   else args.period
    eq = chr(9552)
    print(f"\n{eq * 70}")
    print(f"  EMA CROSSOVER BUY SIGNAL SCANNER")
    print(f"  EMA Fast : {FAST_EMA}   EMA Slow : {SLOW_EMA}   Interval : {INTERVAL}   Period : {PERIOD}")
    print(f"  Mode     : {mode}")
    print(f"  Telegram : {'enabled' if TELEGRAM_ENABLED else 'disabled (add token to enable)'}")
    print(f"  Run time : {now}")
    print(f"{eq * 70}\n")

    all_signals = []

    for index_name, tickers in INDICES.items():
        unique_tickers = list(dict.fromkeys(tickers))
        print(f"  Scanning {index_name} ({len(unique_tickers)} tickers)...")
        signals = scan(unique_tickers, index_name, lookback)
        print_results(signals, index_name, lookback)

        for s in signals:
            s["index"] = index_name
        all_signals.extend(signals)

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"{eq * 70}")
    print(f"  TOTAL BUY SIGNALS: {len(all_signals)}  ({mode})")
    print(f"{eq * 70}\n")

    # Send ONE consolidated Telegram message with all signals
    tg_msg = format_telegram(all_signals, lookback, INTERVAL, now)
    send_telegram(tg_msg)

    if not args.no_csv:
        export_csv(all_signals)
