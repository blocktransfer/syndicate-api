import boto3, hashlib, random

BASE32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
PII_DB = boto3.resource("dynamodb").Table("PII")
BAD_WORDS = ["2G1C", "A55", "ADULT", "ALLA", "ANAL", "ANIL", "ANTI", "ANUS", "AR5E", "ARSE", "ASS", "BABE", "BANG", "BAREBACK", "BASTARD", "BASTINADO", "BBW", "BDSM", "BEANER", "BEANERS", "BI7CH", "BIMBOS", "BIRDLOCK", "BITCH", "BLOWJOB", "BLUMPKIN", "BOLLOCKS", "BOMB", "BONDAGE", "BONER", "BOOB", "BOOOB", "BOY", "BRA", "BUKKAKE", "BULLDYKE", "BUSTY", "BUTT", "CANCER", "CATHOLIC", "CHINK", "CHRIST", "CIALIS", "CLIFF", "CLIT", "CLITORIS", "COCK", "COON", "COONS", "COX", "CREAMPI", "CUM", "CUNT", "DAMN", "DARKI", "DICK", "DIE", "DILDO", "DOGG", "DOLCETT", "DOMMES", "DOOSH", "DRUNK", "DTC", "DUCHE", "DUMB", "DVDA", "DYKE", "ECCHI", "EJACUL", "EROTIC", "EROTISM", "ESCORT", "EUNUCH", "F4NNY", "FAG", "FART", "FCUK", "FECAL", "FECK", "FELCH", "FELLATIO", "FELTCH", "FEMDOM", "FIGGING", "FINGERING", "FISTING", "FOOTJOB", "FREAK", "FROTTING", "FUC", "FUCK", "FUK", "FUTANARI", "FUX", "GANGBANG", "GASM", "GAY", "GENITALS", "GIRL", "GOAT", "GOD", "GOKKUN", "GROPE", "GSPOT", "GURO", "HANDJOB", "HARDCORE", "HELL", "HELP", "HENTAI", "HOAR", "HOLE", "HOMO", "HONKEY", "HOOKER", "HORNY", "HUMPING", "INCEST", "ISIS", "ISLAM", "JACKOF", "JAIL", "JERK", "JESUS", "JEW", "JIGABOO", "JIGGABOO", "JIGGERBOO", "JIZZ", "JUGGS", "KIKE", "KILL", "KINBAKU", "KINKSTER", "KINKY", "KNOBBING", "KUM", "KYS", "LABIA", "LGBT", "LICK", "LMFAO", "LOL", "LUST", "MAN", "MILF", "MOFO", "MOL3ST", "MOLEST", "MONG", "MOTHER", "MURDER", "MUSLIM", "NAKED", "NAMBLA", "NAWASHI", "NEGRO", "NEONAZI", "NIG", "NIPPL", "NSFW", "NUDE", "NUDITY", "NUTTEN", "NYMPHO", "OMG", "OMORASHI","ORGY", "P33", "PAKI", "PANTIES", "PANTY", "PEDO", "PEDOBEAR", "PEDOPHILE", "PEE", "PEGGING", "PENIS", "PHILIA", "PHOBE", "PHUC", "PHUK", "PIKEY", "PISS", "PLAYBOY", "PONYPLAY", "POO", "PORN", "PRICK", "PTHC", "PUBES", "PUNANY", "PUSS", "QUEAF", "QUEEF", "QUIM", "RACIST", "RAGHEAD", "RAPE", "RAPING", "RAPIST", "RECT", "RETARD", "RIMJOB", "RIMMING", "SACC", "SACK", "SADISM", "SAINT", "SANTORUM", "SCAT", "SCHLONG", "SCREW", "SCROTUM", "SCUM", "SEMEN", "SEX", "SHEMALE", "SHIBARI", "SHIT", "SHLONG", "SHOOT", "SHOTA", "SHRIMP", "SKANK", "SKEET", "SLANTEYE", "SLUT", "SMUT", "SNATCH", "SOB", "SODOMIZE", "SODOMY", "SPASTIC", "SPIC", "SPLOOGE", "SPOOGE", "SPUNK", "STRAP", "SUCK", "SWASTIKA", "SWING", "TARD", "TERROR", "THOT", "THREESOME", "THROAT", "TIT", "TOOT", "TOPLES", "TOSSER", "TOWELHEAD", "TRANN", "TRANS", "TRIBADISM", "TUSHY", "TWAT", "TWINK", "UPSKIRT", "UROPHILIA", "VAG", "VIAGRA", "VIBRAT", "VOYEUR", "VOYUER", "VULVA", "WANK", "WETBA", "WHOR", "WOMAN", "WTF", "XXX", "YAOI", "YIFFY"]

def lambda_handler(event, context):
  base = "".join(random.choices(BASE32_ALPHABET, k = 8))
  checksum = getFirst8charChecksum(base)
  ID = base + checksum
  return lambda_handler(event, context) if (
    any(w in ID for w in BAD_WORDS) or
    alreadyExists(ID) or
    ID.isdigit()
  ) else ID

def getFirst8charChecksum(IDfirst8):
  return BASE32_ALPHABET[
    int(
      hashlib.sha3_256(
        IDfirst8.encode()
      ).hexdigest(),
      16
    ) % 32
  ]

def alreadyExists(ID):
  try:
    response = PII_DB.query(
      IndexName = "users",
      KeyConditionExpression = "ID = :val",
      ExpressionAttributeValues = {":val": ID}
    )
    if not response["Count"]:
      return False
  except Exception:
    print(f"PII DB error")
  return True
