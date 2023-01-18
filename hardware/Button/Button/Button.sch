EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L 228EM:228EMVARGBFR S1
U 1 1 634DB931
P 2600 3100
F 0 "S1" H 3300 3365 50  0000 C CNN
F 1 "228EMVARGBFR" H 3300 3274 50  0000 C CNN
F 2 "228EMVARGBFR" H 3850 3200 50  0001 L CNN
F 3 "https://www.mouser.com/datasheet/2/96/228E-1660580.pdf" H 3850 3100 50  0001 L CNN
F 4 "Tactile Switches LED tact sw, gullwing, vertical, red,green&blue flat led" H 3850 3000 50  0001 L CNN "Description"
F 5 "5.5" H 3850 2900 50  0001 L CNN "Height"
F 6 "CTS" H 3850 2800 50  0001 L CNN "Manufacturer_Name"
F 7 "228EMVARGBFR" H 3850 2700 50  0001 L CNN "Manufacturer_Part_Number"
F 8 "774-228EMVARGBFR" H 3850 2600 50  0001 L CNN "Mouser Part Number"
F 9 "https://www.mouser.co.uk/ProductDetail/CTS-Electronic-Components/228EMVARGBFR?qs=BJlw7L4Cy7%2FeuEuJlsaHQw%3D%3D" H 3850 2500 50  0001 L CNN "Mouser Price/Stock"
F 10 "" H 3850 2400 50  0001 L CNN "Arrow Part Number"
F 11 "" H 3850 2300 50  0001 L CNN "Arrow Price/Stock"
F 12 "" H 3850 2200 50  0001 L CNN "Mouser Testing Part Number"
F 13 "" H 3850 2100 50  0001 L CNN "Mouser Testing Price/Stock"
	1    2600 3100
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_01x05 J1
U 1 1 63BAF900
P 4650 3300
F 0 "J1" H 4750 3350 50  0000 L CNN
F 1 "Conn_01x05" H 4730 3251 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Horizontal" H 4650 3300 50  0001 C CNN
F 3 "~" H 4650 3300 50  0001 C CNN
	1    4650 3300
	1    0    0    -1  
$EndComp
Wire Wire Line
	4000 3100 4450 3100
Wire Wire Line
	4000 3200 4200 3200
Wire Wire Line
	4000 3300 4450 3300
Wire Wire Line
	4000 3400 4200 3400
Wire Wire Line
	4200 3400 4200 3200
Connection ~ 4200 3200
Wire Wire Line
	4200 3200 4450 3200
Wire Wire Line
	2600 3300 2450 3300
Wire Wire Line
	2450 3300 2450 3600
Wire Wire Line
	2450 3600 4300 3600
Wire Wire Line
	4300 3600 4300 3400
Wire Wire Line
	4300 3400 4450 3400
Wire Wire Line
	2600 3200 2350 3200
Wire Wire Line
	2350 3200 2350 3700
Wire Wire Line
	2350 3700 4400 3700
Wire Wire Line
	4400 3700 4400 3500
Wire Wire Line
	4400 3500 4450 3500
$EndSCHEMATC
