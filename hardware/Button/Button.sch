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
P 4750 3550
F 0 "S1" H 5450 3815 50  0000 C CNN
F 1 "228EMVARGBFR" H 5450 3724 50  0000 C CNN
F 2 "228EMVARGBFR" H 6000 3650 50  0001 L CNN
F 3 "https://www.mouser.com/datasheet/2/96/228E-1660580.pdf" H 6000 3550 50  0001 L CNN
F 4 "Tactile Switches LED tact sw, gullwing, vertical, red,green&blue flat led" H 6000 3450 50  0001 L CNN "Description"
F 5 "5.5" H 6000 3350 50  0001 L CNN "Height"
F 6 "CTS" H 6000 3250 50  0001 L CNN "Manufacturer_Name"
F 7 "228EMVARGBFR" H 6000 3150 50  0001 L CNN "Manufacturer_Part_Number"
F 8 "774-228EMVARGBFR" H 6000 3050 50  0001 L CNN "Mouser Part Number"
F 9 "https://www.mouser.co.uk/ProductDetail/CTS-Electronic-Components/228EMVARGBFR?qs=BJlw7L4Cy7%2FeuEuJlsaHQw%3D%3D" H 6000 2950 50  0001 L CNN "Mouser Price/Stock"
F 10 "" H 6000 2850 50  0001 L CNN "Arrow Part Number"
F 11 "" H 6000 2750 50  0001 L CNN "Arrow Price/Stock"
F 12 "" H 6000 2650 50  0001 L CNN "Mouser Testing Part Number"
F 13 "" H 6000 2550 50  0001 L CNN "Mouser Testing Price/Stock"
	1    4750 3550
	1    0    0    -1  
$EndComp
Text Label 8300 3550 2    50   ~ 0
BUTTON
Text Label 8300 3750 2    50   ~ 0
LED2_R
Text Label 8300 3650 2    50   ~ 0
LED2_G
Text Label 8300 3850 2    50   ~ 0
LED2_B
$Comp
L power:GND #PWR0103
U 1 1 63C9D06D
P 8250 3950
F 0 "#PWR0103" H 8250 3700 50  0001 C CNN
F 1 "GND" H 8255 3777 50  0000 C CNN
F 2 "" H 8250 3950 50  0001 C CNN
F 3 "" H 8250 3950 50  0001 C CNN
	1    8250 3950
	1    0    0    -1  
$EndComp
$Comp
L power:+3V3 #PWR0104
U 1 1 63C9E7C1
P 8250 3450
F 0 "#PWR0104" H 8250 3300 50  0001 C CNN
F 1 "+3V3" H 8265 3623 50  0000 C CNN
F 2 "" H 8250 3450 50  0001 C CNN
F 3 "" H 8250 3450 50  0001 C CNN
	1    8250 3450
	1    0    0    -1  
$EndComp
$Comp
L Device:R R2
U 1 1 63CD680C
P 7350 3750
F 0 "R2" V 7250 3650 50  0000 C CNN
F 1 "150R" V 7250 3850 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal" V 7235 3750 50  0001 C CNN
F 3 "~" H 7350 3750 50  0001 C CNN
	1    7350 3750
	0    1    1    0   
$EndComp
$Comp
L Device:R R1
U 1 1 63CDB62E
P 7650 3850
F 0 "R1" V 7550 3750 50  0000 C CNN
F 1 "150R" V 7550 3950 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal" V 7535 3850 50  0001 C CNN
F 3 "~" H 7650 3850 50  0001 C CNN
	1    7650 3850
	0    1    1    0   
$EndComp
Wire Wire Line
	7500 3750 8300 3750
NoConn ~ 4750 3550
$Comp
L Connector_Generic:Conn_01x06 J2
U 1 1 63C7BE05
P 8500 3650
F 0 "J2" H 8580 3692 50  0000 L CNN
F 1 "Button connector" H 8580 3601 50  0000 L CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_1x06_P2.54mm_Horizontal" H 8500 3650 50  0001 C CNN
F 3 "~" H 8500 3650 50  0001 C CNN
	1    8500 3650
	1    0    0    -1  
$EndComp
Connection ~ 8250 3450
Wire Wire Line
	8250 3450 8300 3450
Connection ~ 8250 3950
Wire Wire Line
	8250 3950 8300 3950
Wire Wire Line
	6500 3950 8250 3950
Wire Wire Line
	6650 3450 8250 3450
Wire Wire Line
	6500 3950 6500 3650
Wire Wire Line
	6500 3650 6150 3650
Wire Wire Line
	6650 3450 6650 3850
Wire Wire Line
	6650 3850 6150 3850
Wire Wire Line
	6150 3550 8300 3550
Wire Wire Line
	6800 3650 6800 3750
Wire Wire Line
	6800 3750 6150 3750
Wire Wire Line
	6800 3650 7500 3650
Wire Wire Line
	7200 3750 6950 3750
Wire Wire Line
	6950 3750 6950 4100
Wire Wire Line
	6950 4100 4750 4100
Wire Wire Line
	4750 4100 4750 3750
Wire Wire Line
	7500 3850 7200 3850
Wire Wire Line
	7200 3850 7200 4200
Wire Wire Line
	7200 4200 4650 4200
Wire Wire Line
	4650 4200 4650 3650
Wire Wire Line
	4650 3650 4750 3650
Wire Wire Line
	7800 3850 8300 3850
Wire Wire Line
	7800 3650 8300 3650
$Comp
L Device:R R3
U 1 1 63CDB348
P 7650 3650
F 0 "R3" V 7550 3500 50  0000 C CNN
F 1 "150R" V 7550 3700 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal" V 7535 3650 50  0001 C CNN
F 3 "~" H 7650 3650 50  0001 C CNN
	1    7650 3650
	0    1    1    0   
$EndComp
$EndSCHEMATC
