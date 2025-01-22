from stix_shifter_utils.stix_translation.src.utils.transformers import ValueTransformer
from stix_shifter_utils.utils import logger
from datetime import datetime, timezone

logger = logger.set_logger(__name__)

class EpochToTimestamp(ValueTransformer):
    """A value transformer for converting Unix epoch timestamps to ISO format"""
    
    @staticmethod
    def transform(epoch):
        try:
            # Convert milliseconds to seconds if timestamp is too large
            epoch_seconds = int(epoch) / 1000 if len(str(int(epoch))) > 10 else int(epoch)
            return (datetime.fromtimestamp(epoch_seconds, timezone.utc)
                    .strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')
        except ValueError:
            logger.error("Cannot convert epoch value {} to timestamp".format(epoch))