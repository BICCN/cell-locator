# LIMS Integration

Integration with a Laboratory Information Management System (LIMS) is achieved through a simple REST api; there are only two endpoints to get and set annotations for a particular specimen.

Support is enabled by command line options {option}`--lims-specimen-id` and {option}`--lims-base-url`, and optionally {option}`--lims-specimen-kind`.

* At application startup time to (1) retrieve the corresponding annotation from LIMS and
  load it by using the `<base-url>/specimen_metadata/view` endpoint and (2) to enable the "Upload Annotation" button
* After user initiate annotation upload to LIMS while using the `<base-url>/specimen_metadata/store` endpoint.

The [`specimen_id`][specimen_id] parameter for both requests is set to the value of {option}`--lims-specimen-id`, and the [`kind`][kind] parameter is set to the value of {option}`--lims-specimen-kind`.

[specimen_id]: https://github.com/KitwareMedical/AllenInstituteMockLIMS#fetch-specimen-metadata
[kind]: https://github.com/KitwareMedical/AllenInstituteMockLIMS#store-specimen-metadata

For testing the functionality a simple [reference LIMS server][lims] is implemented using [flask][flask]; this server is only suitable for testing the API. See [Endpoint Documentation][endpoints] for more information and sample requests.

[flask]: https://github.com/pallets/flask
[lims]: https://github.com/KitwareMedical/AllenInstituteMockLIMS
[endpoints]: https://github.com/KitwareMedical/AllenInstituteMockLIMS#endpoints
