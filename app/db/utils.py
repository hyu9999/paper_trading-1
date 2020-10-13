import pytz
from bson.codec_options import CodecOptions

codec_option = CodecOptions(tz_aware=True, tzinfo=pytz.timezone("Asia/Shanghai"))
