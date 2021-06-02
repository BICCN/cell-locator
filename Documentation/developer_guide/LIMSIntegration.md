# LIMS Integration

Integration with a Laboratory Information Management System (LIMS) is acheived through a simple REST api; there are only two endpoints to get and set annotations for a particular specimen.

The API is described at [KitwareMedical/AllenInstituteMockLIMS][mock], and a simple
[flask][flask] reference implementation is provided (note this implementation does not
persist any data; it is _only_ a demonstration of the API endpoints required, suitable 
only for testing.  

[mock]: https://github.com/KitwareMedical/AllenInstituteMockLIMS
[flask]: https://github.com/pallets/flask
