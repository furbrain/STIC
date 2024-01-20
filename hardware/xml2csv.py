#
# Example python script to generate a BOM from a KiCad generic netlist
#
# Example: Ungrouped (One component per row) CSV output
#

"""
    @package
    Output: CSV (comma-separated)
    Grouped By: ungrouped, one component per line
    Sorted By: Ref
    Fields: Ref, Value, Part, Footprint, Datasheet, Manufacturer, Vendor, DNP

    Command line:
    python "pathToFile/bom_csv_sorted_by_ref.py" "%I" "%O.csv"
"""

from __future__ import print_function

# Import the KiCad python helper module
import kicad_netlist_reader
import kicad_utils
import csv
import sys

# A helper function to filter/convert a string read in netlist
#currently: do nothing
def fromNetlistText( aText ):
    return aText

# Generate an instance of a generic netlist, and load the netlist tree from
# the command line option. If the file doesn't exist, execution will stop
nets = [kicad_netlist_reader.netlist(name) for name in sys.argv[1:]]

f = sys.stdout

# Create a new csv writer object to use as the output formatter
out = csv.writer(f, lineterminator='\n', delimiter=',', quotechar="\"", quoting=csv.QUOTE_ALL)

# override csv.writer's writerow() to support utf8 encoding:
def writerow( acsvwriter, columns ):
    utf8row = []
    for col in columns:
        utf8row.append( fromNetlistText( str(col) ) )
    acsvwriter.writerow( utf8row )

components = []
for net in nets:
    components.extend(net.getInterestingComponents( excludeBOM=True ))
fields = ["Description", "Farnell Part Number", "Manufacturer_Part_Number"]
# Output a field delimited header line
writerow( out, ['Source:', net.getSource()] )
writerow( out, ['Date:', net.getDate()] )
writerow( out, ['Tool:', net.getTool()] )
writerow( out, ['Ref', 'Value', 'Footprint', 'Datasheet', *fields] )

# Output all of the component information (One component per row)
for c in components:
    field_vals = [c.getField(f) for f in fields]
    writerow( out, [c.getRef(), c.getValue(), c.getFootprint(), c.getDatasheet(),
        *field_vals])

