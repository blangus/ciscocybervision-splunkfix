
import ta_cisco_cybervision_declare
from TA_cisco_cybervision_startdate_validation import ValidateStartDate
from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel
)
from splunktaucclib.rest_handler import admin_external, util
from splunk_aoblib.rest_migration import ConfigMigrationHandler
from utils_cybervision import CyberVisionModel, IntervalValidator


util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        'interval',
        required=True,
        encrypted=False,
        default=None,
        validator=IntervalValidator()
    ),
    field.RestField(
        'index',
        required=True,
        encrypted=False,
        default='default',
        validator=validator.String(
            min_len=1,
            max_len=80,
        )
    ),
    field.RestField(
        'global_account',
        required=True,
        encrypted=False,
        default=None,
        validator=None
    ),
    field.RestField(
        'start_date',
        required=True,
        encrypted=False,
        default=None,
        validator=ValidateStartDate()
    ),
    field.RestField(
        'page_size',
        required=False,
        encrypted=False,
        default=10,
        validator=validator.Pattern(
            regex=r"""^\-[1-9]\d*$|^\d*$""",
        )
    ),
    field.RestField(
        'disabled',
        required=False,
        validator=None
    )

]
model = RestModel(fields, name=None)


endpoint = CyberVisionModel(
    'cybervision_components',
    model,
)


if __name__ == '__main__':
    admin_external.handle(
        endpoint,
        handler=ConfigMigrationHandler,
    )
