 %module gml_scanner
 %{
 /* Includes the header in the wrapper code */
 #include "gml_scanner.h"
 %}
 
 /* Parse the header file to generate wrappers */
 %include "gml_scanner.h"
 