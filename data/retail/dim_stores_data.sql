USE IDENTIFIER(:database);

-- Insert store data for BrickMart retail chain
INSERT INTO stores (
    store_id, store_name, store_address, store_city, store_state, store_zipcode, 
    store_country, store_phone, store_email, store_manager_id, opening_date, 
    store_area_sqft, is_open_24_hours, latitude, longitude, region_id
) VALUES
-- New York Area Stores
('001', 'BrickMart Downtown', '123 Main St', 'New York', 'NY', '10001', 'USA', '(212) 555-1234', 'downtown@brickmart.com', 'mgr_001', '2015-05-20', 5000.0, true, 40.7128, -74.006, '1'),
('002', 'BrickMart Uptown', '456 Broadway', 'New York', 'NY', '10002', 'USA', '(212) 555-5678', 'uptown@brickmart.com', 'mgr_002', '2018-07-15', 3000.0, false, 40.7138, -74.007, '1'),
('003', 'BrickMart Manhattan Mini', '789 5th Avenue', 'New York', 'NY', '10003', 'USA', '(212) 555-9012', 'manhattanmini@brickmart.com', 'mgr_003', '2016-03-10', 2500.0, true, 40.7589, -73.9851, '1'),
('004', 'BrickMart Bronx', '321 Fordham Road', 'New York', 'NY', '10458', 'USA', '(718) 555-3456', 'bronx@brickmart.com', 'mgr_004', '2017-08-22', 4500.0, false, 40.8614, -73.8827, '1'),
('005', 'BrickMart Queens Corner', '567 Queens Blvd', 'New York', 'NY', '11375', 'USA', '(718) 555-7890', 'queens@brickmart.com', 'mgr_005', '2019-01-15', 3800.0, true, 40.7282, -73.8618, '1'),
('006', 'BrickMart Brooklyn Heights', '123 Montague St', 'New York', 'NY', '11201', 'USA', '(718) 555-4321', 'brooklyn@brickmart.com', 'mgr_006', '2020-03-01', 2800.0, false, 40.6935, -73.9916, '1'),
('007', 'BrickMart Staten Island', '789 Hylan Blvd', 'New York', 'NY', '10305', 'USA', '(718) 555-8765', 'statenisland@brickmart.com', 'mgr_007', '2018-06-15', 4200.0, true, 40.6065, -74.0752, '1'),
('008', 'BrickMart Harlem', '456 Malcolm X Blvd', 'New York', 'NY', '10027', 'USA', '(212) 555-9876', 'harlem@brickmart.com', 'mgr_008', '2017-11-30', 3500.0, false, 40.8116, -73.9465, '1'),
('009', 'BrickMart Lower East Side', '234 Delancey St', 'New York', 'NY', '10002', 'USA', '(212) 555-3456', 'les@brickmart.com', 'mgr_009', '2019-08-22', 2600.0, true, 40.7168, -73.9861, '1'),

-- Boston Area Stores
('010', 'BrickMart Back Bay', '100 Boylston St', 'Boston', 'MA', '02116', 'USA', '(617) 555-1234', 'backbay@brickmart.com', 'mgr_010', '2018-03-15', 3200.0, false, 42.3518, -71.0711, '1'),
('011', 'BrickMart Beacon Hill', '89 Charles St', 'Boston', 'MA', '02114', 'USA', '(617) 555-2345', 'beaconhill@brickmart.com', 'mgr_011', '2019-05-01', 2800.0, false, 42.356, -71.0705, '1'),
('012', 'BrickMart South End', '540 Tremont St', 'Boston', 'MA', '02118', 'USA', '(617) 555-3456', 'southend@brickmart.com', 'mgr_012', '2017-09-12', 3500.0, true, 42.3433, -71.0726, '1'),
('013', 'BrickMart Fenway', '123 Brookline Ave', 'Boston', 'MA', '02215', 'USA', '(617) 555-4567', 'fenway@brickmart.com', 'mgr_013', '2020-01-15', 4000.0, false, 42.3467, -71.0972, '1'),
('014', 'BrickMart Cambridge', '750 Memorial Dr', 'Boston', 'MA', '02139', 'USA', '(617) 555-5678', 'cambridge@brickmart.com', 'mgr_014', '2018-11-30', 3800.0, true, 42.3576, -71.1009, '1'),

-- Philadelphia Area Stores
('015', 'BrickMart Center City', '1200 Market St', 'Philadelphia', 'PA', '19107', 'USA', '(215) 555-1234', 'centercity@brickmart.com', 'mgr_015', '2019-04-01', 4500.0, true, 39.9526, -75.1652, '1'),
('016', 'BrickMart South Philly', '1001 S 9th St', 'Philadelphia', 'PA', '19147', 'USA', '(215) 555-2345', 'southphilly@brickmart.com', 'mgr_016', '2017-07-15', 3300.0, false, 39.9375, -75.1571, '1'),
('017', 'BrickMart University City', '3401 Walnut St', 'Philadelphia', 'PA', '19104', 'USA', '(215) 555-3456', 'univcity@brickmart.com', 'mgr_017', '2020-02-28', 2900.0, true, 39.9522, -75.1932, '1'),
('018', 'BrickMart Northern Liberties', '180 W Girard Ave', 'Philadelphia', 'PA', '19123', 'USA', '(215) 555-4567', 'noliberties@brickmart.com', 'mgr_018', '2018-09-01', 3700.0, false, 39.9697, -75.1398, '1'),
('019', 'BrickMart Rittenhouse Square', '1800 Walnut St', 'Philadelphia', 'PA', '19103', 'USA', '(215) 555-5678', 'rittenhouse@brickmart.com', 'mgr_019', '2019-11-15', 4100.0, true, 39.9496, -75.1709, '1'),

-- Washington DC Area Stores
('020', 'BrickMart Georgetown', '1200 Wisconsin Ave NW', 'Washington D.C.', 'DC', '20007', 'USA', '(202) 555-1234', 'georgetown@brickmart.com', 'mgr_020', '2018-04-15', 3800.0, false, 38.9055, -77.067, '2'),
('021', 'BrickMart Dupont Circle', '1800 P St NW', 'Washington D.C.', 'DC', '20036', 'USA', '(202) 555-2345', 'dupont@brickmart.com', 'mgr_021', '2019-06-01', 3200.0, true, 38.9097, -77.0409, '2'),
('022', 'BrickMart Capitol Hill', '400 East Capitol St NE', 'Washington D.C.', 'DC', '20003', 'USA', '(202) 555-3456', 'capitolhill@brickmart.com', 'mgr_022', '2017-08-30', 2900.0, false, 38.8898, -77.0001, '2'),
('023', 'BrickMart Adams Morgan', '1700 Columbia Rd NW', 'Washington D.C.', 'DC', '20009', 'USA', '(202) 555-4567', 'adamsmorgan@brickmart.com', 'mgr_023', '2020-03-15', 3500.0, true, 38.9222, -77.0421, '2'),
('024', 'BrickMart U Street', '1400 U St NW', 'Washington D.C.', 'DC', '20009', 'USA', '(202) 555-5678', 'ustreet@brickmart.com', 'mgr_024', '2019-09-01', 3100.0, false, 38.9169, -77.0312, '2'),

-- Baltimore Area Stores
('025', 'BrickMart Inner Harbor', '600 E Pratt St', 'Baltimore', 'MD', '21202', 'USA', '(410) 555-1234', 'innerharbor@brickmart.com', 'mgr_025', '2018-07-01', 4200.0, true, 39.2866, -76.6089, '2'),
('026', 'BrickMart Fells Point', '1700 Thames St', 'Baltimore', 'MD', '21231', 'USA', '(410) 555-2345', 'fellspoint@brickmart.com', 'mgr_026', '2019-04-15', 3300.0, false, 39.2819, -76.5943, '2'),
('027', 'BrickMart Canton', '2800 O''Donnell St', 'Baltimore', 'MD', '21224', 'USA', '(410) 555-3456', 'canton@brickmart.com', 'mgr_027', '2017-11-30', 3600.0, true, 39.2792, -76.5762, '2'),
('028', 'BrickMart Federal Hill', '1000 Light St', 'Baltimore', 'MD', '21230', 'USA', '(410) 555-4567', 'fedhill@brickmart.com', 'mgr_028', '2020-01-15', 2800.0, false, 39.2775, -76.6134, '2'),
('029', 'BrickMart Mount Vernon', '600 N Charles St', 'Baltimore', 'MD', '21201', 'USA', '(410) 555-5678', 'mtvernon@brickmart.com', 'mgr_029', '2019-08-01', 3400.0, true, 39.2967, -76.6156, '2'),

-- Richmond Area Stores
('030', 'BrickMart Carytown', '3500 W Cary St', 'Richmond', 'VA', '23221', 'USA', '(804) 555-1234', 'carytown@brickmart.com', 'mgr_030', '2018-05-15', 3700.0, false, 37.5552, -77.4856, '2'),
('031', 'BrickMart Shockoe Bottom', '1800 E Main St', 'Richmond', 'VA', '23223', 'USA', '(804) 555-2345', 'shockoe@brickmart.com', 'mgr_031', '2019-03-01', 3200.0, true, 37.5315, -77.4267, '2'),
('032', 'BrickMart Fan District', '2200 W Main St', 'Richmond', 'VA', '23220', 'USA', '(804) 555-3456', 'fandistrict@brickmart.com', 'mgr_032', '2017-10-15', 2900.0, false, 37.5539, -77.4673, '2'),
('033', 'BrickMart Scott''s Addition', '3000 W Broad St', 'Richmond', 'VA', '23230', 'USA', '(804) 555-4567', 'scottsadd@brickmart.com', 'mgr_033', '2020-02-01', 3800.0, true, 37.5668, -77.4747, '2'),
('034', 'BrickMart Church Hill', '2500 E Broad St', 'Richmond', 'VA', '23223', 'USA', '(804) 555-5678', 'churchhill@brickmart.com', 'mgr_034', '2019-07-15', 3100.0, false, 37.5338, -77.4178, '2'),

-- Atlanta Area Stores
('036', 'BrickMart Buckhead', '3255 Peachtree Rd', 'Atlanta', 'GA', '30305', 'USA', '(404) 555-1234', 'buckhead@brickmart.com', 'mgr_036', '2017-05-15', 4200.0, false, 33.8406, -84.3795, '3'),
('037', 'BrickMart Midtown Atlanta', '950 W Peachtree St', 'Atlanta', 'GA', '30309', 'USA', '(404) 555-2345', 'midtown@brickmart.com', 'mgr_037', '2019-03-01', 3500.0, true, 33.7815, -84.3885, '3'),
('046', 'BrickMart Midtown West', '950 West Peachtree St NW', 'Atlanta', 'GA', '30309', 'USA', '(404) 555-1234', 'midtownatl@brickmart.com', 'mgr_046', '2018-04-15', 3400.0, true, 33.7815, -84.3857, '3'),
('047', 'BrickMart Buckhead North', '3035 Peachtree Rd NE', 'Atlanta', 'GA', '30305', 'USA', '(404) 555-2345', 'buckheadnorth@brickmart.com', 'mgr_047', '2017-12-10', 3800.0, false, 33.8399, -84.3801, '3'),
('048', 'BrickMart Virginia Highland', '1001 Virginia Ave NE', 'Atlanta', 'GA', '30306', 'USA', '(404) 555-3456', 'vahighland@brickmart.com', 'mgr_048', '2019-02-20', 2700.0, false, 33.7817, -84.3571, '3'),
('049', 'BrickMart Little Five Points', '421 Moreland Ave NE', 'Atlanta', 'GA', '30307', 'USA', '(404) 555-4567', 'l5p@brickmart.com', 'mgr_049', '2018-09-05', 2500.0, true, 33.7618, -84.349, '3'),
('050', 'BrickMart West Midtown', '1100 Howell Mill Rd NW', 'Atlanta', 'GA', '30318', 'USA', '(404) 555-5678', 'westmidtown@brickmart.com', 'mgr_050', '2020-01-15', 3300.0, false, 33.7861, -84.4113, '3'),

-- Miami Area Stores
('038', 'BrickMart South Beach', '1020 Ocean Dr', 'Miami', 'FL', '33139', 'USA', '(305) 555-1234', 'southbeach@brickmart.com', 'mgr_038', '2018-12-01', 2900.0, true, 25.7825, -80.1324, '3'),
('039', 'BrickMart Brickell', '901 S Miami Ave', 'Miami', 'FL', '33130', 'USA', '(305) 555-2345', 'brickell@brickmart.com', 'mgr_039', '2017-09-15', 3800.0, false, 25.7657, -80.1937, '3'),
('041', 'BrickMart Little Havana', '1200 SW 8th St', 'Miami', 'FL', '33135', 'USA', '(305) 555-3456', 'littlehavana@brickmart.com', 'mgr_041', '2019-03-15', 3200.0, true, 25.7655, -80.2179, '3'),
('042', 'BrickMart Wynwood', '250 NW 24th St', 'Miami', 'FL', '33127', 'USA', '(305) 555-4567', 'wynwood@brickmart.com', 'mgr_042', '2020-01-10', 2900.0, false, 25.7994, -80.1989, '3'),
('043', 'BrickMart Coral Gables', '2200 Ponce de Leon Blvd', 'Miami', 'FL', '33134', 'USA', '(305) 555-5678', 'coralgables@brickmart.com', 'mgr_043', '2017-11-20', 3500.0, false, 25.7501, -80.259, '3'),
('044', 'BrickMart Coconut Grove', '3330 Grand Ave', 'Miami', 'FL', '33133', 'USA', '(305) 555-6789', 'coconutgrove@brickmart.com', 'mgr_044', '2018-08-05', 2600.0, true, 25.7269, -80.2425, '3'),
('045', 'BrickMart Downtown Miami', '100 SE 2nd St', 'Miami', 'FL', '33131', 'USA', '(305) 555-7890', 'downtown@brickmart.com', 'mgr_045', '2019-06-01', 3100.0, true, 25.7743, -80.1937, '3'),

-- Charlotte Area Stores
('040', 'BrickMart Dilworth', '1235 East Blvd', 'Charlotte', 'NC', '28203', 'USA', '(704) 555-1234', 'dilworth@brickmart.com', 'mgr_040', '2019-04-01', 3300.0, false, 35.2089, -80.8486, '3'),
('051', 'BrickMart South End', '2100 South Blvd', 'Charlotte', 'NC', '28203', 'USA', '(704) 555-1234', 'southend@brickmart.com', 'mgr_051', '2019-03-15', 3500.0, true, 35.2098, -80.8577, '3'),
('052', 'BrickMart NoDa', '3201 N Davidson St', 'Charlotte', 'NC', '28205', 'USA', '(704) 555-2345', 'noda@brickmart.com', 'mgr_052', '2018-07-01', 2800.0, false, 35.2424, -80.8024, '3'),
('053', 'BrickMart Plaza Midwood', '1600 Central Ave', 'Charlotte', 'NC', '28205', 'USA', '(704) 555-3456', 'plazamidwood@brickmart.com', 'mgr_053', '2017-11-15', 3200.0, true, 35.2206, -80.8099, '3'),
('054', 'BrickMart Uptown', '300 S Tryon St', 'Charlotte', 'NC', '28202', 'USA', '(704) 555-4567', 'uptown@brickmart.com', 'mgr_054', '2020-02-01', 2900.0, true, 35.2271, -80.8431, '3'),
('055', 'BrickMart Myers Park', '1024 Providence Rd', 'Charlotte', 'NC', '28207', 'USA', '(704) 555-5678', 'myerspark@brickmart.com', 'mgr_055', '2019-08-15', 3800.0, false, 35.2033, -80.8241, '3'),

-- Chicago Area Stores
('056', 'BrickMart Loop', '200 N Michigan Ave', 'Chicago', 'IL', '60601', 'USA', '(312) 555-1234', 'loop@brickmart.com', 'mgr_056', '2018-05-01', 4200.0, true, 41.8857, -87.6244, '4'),
('057', 'BrickMart Wicker Park', '1600 N Milwaukee Ave', 'Chicago', 'IL', '60647', 'USA', '(312) 555-2345', 'wickerpark@brickmart.com', 'mgr_057', '2019-06-15', 3500.0, false, 41.9103, -87.6731, '4'),
('058', 'BrickMart Lincoln Park', '2400 N Clark St', 'Chicago', 'IL', '60614', 'USA', '(312) 555-3456', 'lincolnpark@brickmart.com', 'mgr_058', '2017-09-01', 3800.0, true, 41.9256, -87.6412, '4'),
('059', 'BrickMart Logan Square', '2800 N Milwaukee Ave', 'Chicago', 'IL', '60618', 'USA', '(312) 555-4567', 'logan@brickmart.com', 'mgr_059', '2020-03-01', 3100.0, false, 41.9302, -87.7024, '4'),
('060', 'BrickMart River North', '500 N State St', 'Chicago', 'IL', '60654', 'USA', '(312) 555-5678', 'rivernorth@brickmart.com', 'mgr_060', '2019-04-15', 4000.0, true, 41.8907, -87.6278, '4'),

-- Detroit Area Stores
('061', 'BrickMart Midtown Detroit', '4400 Woodward Ave', 'Detroit', 'MI', '48201', 'USA', '(313) 555-1234', 'midtown@brickmart.com', 'mgr_061', '2018-08-01', 3600.0, true, 42.3516, -83.0602, '4'),
('062', 'BrickMart Corktown', '1700 Michigan Ave', 'Detroit', 'MI', '48216', 'USA', '(313) 555-2345', 'corktown@brickmart.com', 'mgr_062', '2019-05-15', 3200.0, false, 42.3316, -83.0768, '4'),
('063', 'BrickMart Eastern Market', '2934 Russell St', 'Detroit', 'MI', '48207', 'USA', '(313) 555-3456', 'easternmarket@brickmart.com', 'mgr_063', '2017-12-01', 4100.0, true, 42.3476, -83.0419, '4'),
('064', 'BrickMart New Center', '3011 W Grand Blvd', 'Detroit', 'MI', '48202', 'USA', '(313) 555-4567', 'newcenter@brickmart.com', 'mgr_064', '2020-02-15', 3400.0, false, 42.3702, -83.0751, '4'),
('065', 'BrickMart Rivertown', '1600 E Jefferson Ave', 'Detroit', 'MI', '48207', 'USA', '(313) 555-5678', 'rivertown@brickmart.com', 'mgr_065', '2019-07-01', 3700.0, true, 42.3366, -83.0297, '4'),

-- Indianapolis Area Stores
('066', 'BrickMart Mass Ave', '400 Massachusetts Ave', 'Indianapolis', 'IN', '46204', 'USA', '(317) 555-1234', 'massave@brickmart.com', 'mgr_066', '2018-06-15', 3300.0, true, 39.7703, -86.1519, '4'),
('067', 'BrickMart Broad Ripple', '6280 N College Ave', 'Indianapolis', 'IN', '46220', 'USA', '(317) 555-2345', 'broadripple@brickmart.com', 'mgr_067', '2019-09-01', 2900.0, false, 39.8703, -86.1445, '4'),
('068', 'BrickMart Fountain Square', '1043 Virginia Ave', 'Indianapolis', 'IN', '46203', 'USA', '(317) 555-3456', 'fountainsq@brickmart.com', 'mgr_068', '2017-10-15', 3100.0, true, 39.7536, -86.142, '4'),
('069', 'BrickMart Downtown Indy', '50 S Meridian St', 'Indianapolis', 'IN', '46204', 'USA', '(317) 555-4567', 'downtownindy@brickmart.com', 'mgr_069', '2020-01-01', 3600.0, true, 39.7668, -86.1577, '4'),

-- Kansas City Area Stores
('134', 'BrickMart Plaza', '4750 Broadway', 'Kansas City', 'MO', '64112', 'USA', '(816) 555-1234', 'plaza@brickmart.com', 'mgr_134', '2018-05-15', 4100.0, true, 39.042, -94.5906, '4'),
('135', 'BrickMart Westport', '4050 Pennsylvania Ave', 'Kansas City', 'MO', '64111', 'USA', '(816) 555-2345', 'westport@brickmart.com', 'mgr_135', '2019-09-01', 3200.0, false, 39.0505, -94.5906, '4'),
('136', 'BrickMart Crossroads', '2020 Baltimore Ave', 'Kansas City', 'MO', '64108', 'USA', '(816) 555-3456', 'crossroads@brickmart.com', 'mgr_136', '2017-10-15', 2900.0, true, 39.0914, -94.5836, '4'),
('137', 'BrickMart River Market', '411 Delaware St', 'Kansas City', 'MO', '64105', 'USA', '(816) 555-4567', 'rivermarket@brickmart.com', 'mgr_137', '2020-04-01', 3600.0, false, 39.1089, -94.5829, '4'),

-- Phoenix Area Stores
('070', 'BrickMart Downtown Phoenix', '333 E Jefferson St', 'Phoenix', 'AZ', '85004', 'USA', '(602) 555-1234', 'dtphoenix@brickmart.com', 'mgr_070', '2018-06-15', 4200.0, true, 33.4484, -112.074, '5'),
('071', 'BrickMart Scottsdale', '7014 E Camelback Rd', 'Phoenix', 'AZ', '85251', 'USA', '(602) 555-2345', 'scottsdale@brickmart.com', 'mgr_071', '2019-03-01', 3800.0, false, 33.4994, -111.9289, '5'),
('072', 'BrickMart Tempe', '2000 E Rio Salado Pkwy', 'Phoenix', 'AZ', '85281', 'USA', '(602) 555-3456', 'tempe@brickmart.com', 'mgr_072', '2017-08-15', 4500.0, true, 33.4316, -111.9083, '5'),
('073', 'BrickMart Glendale', '7700 W Arrowhead Towne Center', 'Phoenix', 'AZ', '85308', 'USA', '(602) 555-4567', 'glendale@brickmart.com', 'mgr_073', '2020-01-10', 3200.0, false, 33.6377, -112.215, '5'),
('074', 'BrickMart Mesa', '1230 S Val Vista Dr', 'Phoenix', 'AZ', '85204', 'USA', '(602) 555-5678', 'mesa@brickmart.com', 'mgr_074', '2019-05-20', 3600.0, true, 33.3903, -111.7516, '5'),

-- Las Vegas Area Stores
('075', 'BrickMart Strip', '3500 Las Vegas Blvd S', 'Las Vegas', 'NV', '89109', 'USA', '(702) 555-1234', 'strip@brickmart.com', 'mgr_075', '2018-12-01', 5000.0, true, 36.1147, -115.1728, '6'),
('076', 'BrickMart Downtown Vegas', '301 Fremont St', 'Las Vegas', 'NV', '89101', 'USA', '(702) 555-2345', 'downtownvegas@brickmart.com', 'mgr_076', '2017-07-15', 3800.0, true, 36.1699, -115.1398, '6'),
('077', 'BrickMart Summerlin', '1980 Festival Plaza Dr', 'Las Vegas', 'NV', '89135', 'USA', '(702) 555-3456', 'summerlin@brickmart.com', 'mgr_077', '2019-09-01', 4200.0, false, 36.1575, -115.3368, '6'),
('078', 'BrickMart Henderson', '2300 Paseo Verde Pkwy', 'Las Vegas', 'NV', '89052', 'USA', '(702) 555-4567', 'henderson@brickmart.com', 'mgr_078', '2020-02-15', 3500.0, false, 36.0145, -115.0874, '6'),
('079', 'BrickMart Spring Valley', '4178 S Fort Apache Rd', 'Las Vegas', 'NV', '89147', 'USA', '(702) 555-5678', 'springvalley@brickmart.com', 'mgr_079', '2018-04-01', 3300.0, true, 36.1087, -115.2977, '6'),

-- San Francisco Area Stores (Enhanced with more locations)
('080', 'BrickMart Financial District', '343 Sansome St', 'San Francisco', 'CA', '94104', 'USA', '(415) 555-1234', 'fidi@brickmart.com', 'mgr_080', '2017-06-01', 3200.0, false, 37.7936, -122.4014, '6'),
('081', 'BrickMart Mission District', '2558 Mission St', 'San Francisco', 'CA', '94110', 'USA', '(415) 555-2345', 'mission@brickmart.com', 'mgr_081', '2019-08-15', 2800.0, true, 37.7562, -122.4186, '6'),
('082', 'BrickMart Hayes Valley', '432 Octavia St', 'San Francisco', 'CA', '94102', 'USA', '(415) 555-3456', 'hayes@brickmart.com', 'mgr_082', '2018-03-01', 2500.0, false, 37.7765, -122.4242, '6'),
('083', 'BrickMart Marina', '2040 Chestnut St', 'San Francisco', 'CA', '94123', 'USA', '(415) 555-4567', 'marina@brickmart.com', 'mgr_083', '2020-01-15', 3000.0, false, 37.8009, -122.4368, '6'),
('084', 'BrickMart Sunset District', '1200 Irving St', 'San Francisco', 'CA', '94122', 'USA', '(415) 555-5678', 'sunset@brickmart.com', 'mgr_084', '2017-11-01', 3400.0, true, 37.7642, -122.4682, '6'),
('153', 'BrickMart Castro', '2300 Market St', 'San Francisco', 'CA', '94114', 'USA', '(415) 555-6789', 'castro@brickmart.com', 'mgr_153', '2019-04-15', 2900.0, false, 37.7609, -122.4350, '6'),
('154', 'BrickMart Chinatown', '800 Grant Ave', 'San Francisco', 'CA', '94108', 'USA', '(415) 555-7890', 'chinatown@brickmart.com', 'mgr_154', '2018-09-01', 2200.0, true, 37.7946, -122.4058, '6'),
('155', 'BrickMart North Beach', '1650 Stockton St', 'San Francisco', 'CA', '94133', 'USA', '(415) 555-8901', 'northbeach@brickmart.com', 'mgr_155', '2017-12-15', 2600.0, false, 37.8024, -122.4089, '6'),
('156', 'BrickMart Nob Hill', '1200 California St', 'San Francisco', 'CA', '94109', 'USA', '(415) 555-9012', 'nobhill@brickmart.com', 'mgr_156', '2020-03-01', 2800.0, false, 37.7919, -122.4147, '6'),
('157', 'BrickMart SOMA', '350 Townsend St', 'San Francisco', 'CA', '94107', 'USA', '(415) 555-0123', 'soma@brickmart.com', 'mgr_157', '2019-07-15', 3500.0, true, 37.7749, -122.3959, '6'),
('158', 'BrickMart Richmond District', '3800 Geary Blvd', 'San Francisco', 'CA', '94118', 'USA', '(415) 555-1357', 'richmond@brickmart.com', 'mgr_158', '2018-05-20', 3100.0, false, 37.7816, -122.4635, '6'),
('159', 'BrickMart Haight-Ashbury', '1700 Haight St', 'San Francisco', 'CA', '94117', 'USA', '(415) 555-2468', 'haight@brickmart.com', 'mgr_159', '2019-11-01', 2700.0, true, 37.7693, -122.4489, '6'),
('160', 'BrickMart Potrero Hill', '1200 18th St', 'San Francisco', 'CA', '94107', 'USA', '(415) 555-3579', 'potrero@brickmart.com', 'mgr_160', '2020-06-15', 2900.0, false, 37.7615, -122.3972, '6'),
('161', 'BrickMart Presidio Heights', '3200 Sacramento St', 'San Francisco', 'CA', '94115', 'USA', '(415) 555-4680', 'presidio@brickmart.com', 'mgr_161', '2017-08-30', 3300.0, false, 37.7886, -122.4394, '6'),
('162', 'BrickMart Fillmore', '1800 Fillmore St', 'San Francisco', 'CA', '94115', 'USA', '(415) 555-5791', 'fillmore@brickmart.com', 'mgr_162', '2018-10-10', 2800.0, true, 37.7849, -122.4326, '6'),

-- Seattle Area Stores
('085', 'BrickMart Capitol Hill Seattle', '1525 Broadway', 'Seattle', 'WA', '98122', 'USA', '(206) 555-1234', 'caphill@brickmart.com', 'mgr_085', '2018-07-01', 3100.0, true, 47.6147, -122.3207, '7'),
('086', 'BrickMart Ballard', '5701 24th Ave NW', 'Seattle', 'WA', '98107', 'USA', '(206) 555-2345', 'ballard@brickmart.com', 'mgr_086', '2019-04-15', 3600.0, false, 47.6705, -122.3828, '7'),
('087', 'BrickMart Queen Anne', '2121 Queen Anne Ave N', 'Seattle', 'WA', '98109', 'USA', '(206) 555-3456', 'queenanne@brickmart.com', 'mgr_087', '2017-09-01', 2900.0, false, 47.6372, -122.3566, '7'),
('088', 'BrickMart South Lake Union', '400 Fairview Ave N', 'Seattle', 'WA', '98109', 'USA', '(206) 555-4567', 'slu@brickmart.com', 'mgr_088', '2020-03-01', 4000.0, true, 47.6221, -122.3331, '7'),
('089', 'BrickMart West Seattle', '4555 California Ave SW', 'Seattle', 'WA', '98116', 'USA', '(206) 555-5678', 'westseattle@brickmart.com', 'mgr_089', '2018-11-15', 3300.0, false, 47.5613, -122.3872, '7'),

-- Portland Area Stores
('090', 'BrickMart Pearl District', '1231 NW Couch St', 'Portland', 'OR', '97209', 'USA', '(503) 555-1234', 'pearl@brickmart.com', 'mgr_090', '2017-12-01', 3700.0, false, 45.5233, -122.6843, '7'),
('091', 'BrickMart Hawthorne', '3590 SE Hawthorne Blvd', 'Portland', 'OR', '97214', 'USA', '(503) 555-2345', 'hawthorne@brickmart.com', 'mgr_091', '2019-06-15', 2800.0, true, 45.512, -122.6274, '7'),
('092', 'BrickMart Alberta Arts', '1504 NE Alberta St', 'Portland', 'OR', '97211', 'USA', '(503) 555-3456', 'alberta@brickmart.com', 'mgr_092', '2018-08-01', 2600.0, false, 45.5589, -122.6499, '7'),
('093', 'BrickMart Division Street', '3632 SE Division St', 'Portland', 'OR', '97202', 'USA', '(503) 555-4567', 'division@brickmart.com', 'mgr_093', '2020-02-01', 3100.0, true, 45.505, -122.626, '7'),
('094', 'BrickMart Northwest District', '2375 NW Thurman St', 'Portland', 'OR', '97210', 'USA', '(503) 555-5678', 'nwdistrict@brickmart.com', 'mgr_094', '2019-10-15', 3400.0, false, 45.5352, -122.6991, '7'),

-- Boise Area Stores
('095', 'BrickMart Downtown Boise', '821 W Idaho St', 'Boise', 'ID', '83702', 'USA', '(208) 555-1234', 'dtboise@brickmart.com', 'mgr_095', '2018-05-01', 3200.0, true, 43.6167, -116.2023, '7'),
('100', 'BrickMart North End', '1520 N 13th St', 'Boise', 'ID', '83702', 'USA', '(208) 555-6789', 'northend@brickmart.com', 'mgr_100', '2019-06-15', 2800.0, false, 43.6289, -116.202, '7'),
('101', 'BrickMart Boise Bench', '2520 Vista Ave', 'Boise', 'ID', '83705', 'USA', '(208) 555-7890', 'bench@brickmart.com', 'mgr_101', '2017-09-01', 3100.0, true, 43.5923, -116.2157, '7'),
('102', 'BrickMart Hyde Park', '1501 N 13th St', 'Boise', 'ID', '83702', 'USA', '(208) 555-8901', 'hydepark@brickmart.com', 'mgr_102', '2020-03-15', 2600.0, false, 43.6287, -116.2019, '7'),
('103', 'BrickMart East End', '815 Warm Springs Ave', 'Boise', 'ID', '83712', 'USA', '(208) 555-9012', 'eastend@brickmart.com', 'mgr_103', '2018-07-01', 2900.0, true, 43.6127, -116.1891, '7'),

-- Salt Lake City Area Stores
('096', 'BrickMart Sugar House', '2100 S 1100 E', 'Salt Lake City', 'UT', '84106', 'USA', '(801) 555-2345', 'sugarhouse@brickmart.com', 'mgr_096', '2019-03-15', 3500.0, false, 40.7247, -111.8561, '8'),
('104', 'BrickMart Downtown SLC', '400 S State St', 'Salt Lake City', 'UT', '84111', 'USA', '(801) 555-3456', 'dtslc@brickmart.com', 'mgr_104', '2017-11-01', 4200.0, true, 40.7608, -111.891, '8'),
('105', 'BrickMart The Avenues', '402 E 3rd Ave', 'Salt Lake City', 'UT', '84103', 'USA', '(801) 555-4567', 'avenues@brickmart.com', 'mgr_105', '2019-08-15', 2800.0, false, 40.7747, -111.8789, '8'),
('106', 'BrickMart 9th and 9th', '900 E 900 S', 'Salt Lake City', 'UT', '84105', 'USA', '(801) 555-5678', 'ninth@brickmart.com', 'mgr_106', '2018-04-01', 3100.0, true, 40.7508, -111.8646, '8'),
('107', 'BrickMart Capitol Hill SLC', '350 N State St', 'Salt Lake City', 'UT', '84103', 'USA', '(801) 555-6789', 'capitol@brickmart.com', 'mgr_107', '2020-02-01', 2900.0, false, 40.7774, -111.8882, '8'),

-- Denver Area Stores
('097', 'BrickMart LoDo', '1701 Wynkoop St', 'Denver', 'CO', '80202', 'USA', '(303) 555-3456', 'lodo@brickmart.com', 'mgr_097', '2017-08-01', 4000.0, true, 39.7534, -104.9994, '8'),
('108', 'BrickMart Highland', '2532 15th St', 'Denver', 'CO', '80211', 'USA', '(303) 555-7890', 'highland@brickmart.com', 'mgr_108', '2019-05-15', 3200.0, false, 39.7575, -105.0109, '8'),
('109', 'BrickMart Cherry Creek', '2800 E 2nd Ave', 'Denver', 'CO', '80206', 'USA', '(303) 555-8901', 'cherrycreek@brickmart.com', 'mgr_109', '2018-06-01', 3800.0, true, 39.7179, -104.9567, '8'),
('110', 'BrickMart Capitol Hill Denver', '1200 Grant St', 'Denver', 'CO', '80203', 'USA', '(303) 555-9012', 'caphilldenver@brickmart.com', 'mgr_110', '2020-04-01', 2700.0, false, 39.7349, -104.9841, '8'),
('111', 'BrickMart RiNo', '2601 Larimer St', 'Denver', 'CO', '80205', 'USA', '(303) 555-0123', 'rino@brickmart.com', 'mgr_111', '2019-09-15', 3400.0, true, 39.7594, -104.9847, '8'),

-- Colorado Springs Area Stores
('098', 'BrickMart Old Colorado City', '2501 W Colorado Ave', 'Colorado Springs', 'CO', '80904', 'USA', '(719) 555-4567', 'oldcolorado@brickmart.com', 'mgr_098', '2020-01-15', 3300.0, false, 38.8461, -104.8594, '8'),
('112', 'BrickMart Downtown Springs', '115 E Pikes Peak Ave', 'Colorado Springs', 'CO', '80903', 'USA', '(719) 555-1234', 'dtsprings@brickmart.com', 'mgr_112', '2018-03-01', 3600.0, true, 38.8339, -104.8208, '8'),
('113', 'BrickMart Broadmoor', '1 Lake Ave', 'Colorado Springs', 'CO', '80906', 'USA', '(719) 555-2345', 'broadmoor@brickmart.com', 'mgr_113', '2019-07-15', 4100.0, false, 38.7897, -104.848, '8'),
('114', 'BrickMart North Springs', '7915 N Academy Blvd', 'Colorado Springs', 'CO', '80920', 'USA', '(719) 555-3456', 'nsprings@brickmart.com', 'mgr_114', '2017-12-01', 3200.0, true, 38.9327, -104.797, '8'),
('115', 'BrickMart Powers Center', '5640 Powers Center Point', 'Colorado Springs', 'CO', '80920', 'USA', '(719) 555-4567', 'powers@brickmart.com', 'mgr_115', '2019-11-15', 3500.0, false, 38.9018, -104.7474, '8'),

-- Omaha Area Stores
('099', 'BrickMart Old Market', '1022 Howard St', 'Omaha', 'NE', '68102', 'USA', '(402) 555-5678', 'oldmarket@brickmart.com', 'mgr_099', '2018-11-01', 3600.0, true, 41.2565, -95.9345, '9'),
('116', 'BrickMart Dundee', '5001 Underwood Ave', 'Omaha', 'NE', '68132', 'USA', '(402) 555-6789', 'dundee@brickmart.com', 'mgr_116', '2019-04-15', 2800.0, false, 41.2649, -95.9908, '9'),
('117', 'BrickMart Benson', '6051 Maple St', 'Omaha', 'NE', '68104', 'USA', '(402) 555-7890', 'benson@brickmart.com', 'mgr_117', '2017-07-01', 3200.0, true, 41.2841, -95.9977, '9'),
('118', 'BrickMart Aksarben', '2200 S 67th St', 'Omaha', 'NE', '68106', 'USA', '(402) 555-8901', 'aksarben@brickmart.com', 'mgr_118', '2020-05-01', 3400.0, false, 41.2419, -96.0197, '9'),

-- Wichita Area Stores
('129', 'BrickMart Old Town Wichita', '300 N Mead St', 'Wichita', 'KS', '67202', 'USA', '(316) 555-1234', 'oldtown@brickmart.com', 'mgr_129', '2019-04-01', 3100.0, false, 37.6897, -97.3375, '9'),
('130', 'BrickMart College Hill', '3302 E Douglas Ave', 'Wichita', 'KS', '67208', 'USA', '(316) 555-2345', 'collegehill@brickmart.com', 'mgr_130', '2018-08-15', 2800.0, true, 37.6868, -97.2951, '9'),
('131', 'BrickMart Delano', '555 W Douglas Ave', 'Wichita', 'KS', '67213', 'USA', '(316) 555-3456', 'delano@brickmart.com', 'mgr_131', '2017-12-01', 3300.0, false, 37.6868, -97.3475, '9'),
('132', 'BrickMart East Central', '2721 E Central Ave', 'Wichita', 'KS', '67214', 'USA', '(316) 555-4567', 'eastcentral@brickmart.com', 'mgr_132', '2020-01-15', 2900.0, true, 37.6868, -97.3097, '9'),
('133', 'BrickMart Riverside', '924 W Central Ave', 'Wichita', 'KS', '67203', 'USA', '(316) 555-5678', 'riverside@brickmart.com', 'mgr_133', '2019-07-01', 3500.0, false, 37.6868, -97.3597, '9'),

-- Hawaii Stores
('119', 'BrickMart Waikiki Beach', '2255 Kalakaua Ave', 'Honolulu', 'HI', '96815', 'USA', '(808) 555-1234', 'waikiki@brickmart.com', 'mgr_119', '2019-10-15', 3000.0, true, 21.2793, -157.8283, '10'),
('120', 'BrickMart Ala Moana', '1450 Ala Moana Blvd', 'Honolulu', 'HI', '96814', 'USA', '(808) 555-2345', 'alamoana@brickmart.com', 'mgr_120', '2018-06-01', 4200.0, false, 21.2906, -157.843, '10'),
('121', 'BrickMart Kapahulu', '725 Kapahulu Ave', 'Honolulu', 'HI', '96816', 'USA', '(808) 555-3456', 'kapahulu@brickmart.com', 'mgr_121', '2019-03-15', 2800.0, false, 21.2843, -157.815, '10'),
('122', 'BrickMart Kaimuki', '3618 Waialae Ave', 'Honolulu', 'HI', '96816', 'USA', '(808) 555-4567', 'kaimuki@brickmart.com', 'mgr_122', '2017-11-01', 3100.0, false, 21.2824, -157.7989, '10'),
('123', 'BrickMart Manoa Valley', '2752 Woodlawn Dr', 'Honolulu', 'HI', '96822', 'USA', '(808) 555-5678', 'manoa@brickmart.com', 'mgr_123', '2020-02-15', 2900.0, false, 21.3097, -157.8099, '10'),

-- Alaska Stores
('124', 'BrickMart Downtown Anchorage', '320 W 5th Ave', 'Anchorage', 'AK', '99501', 'USA', '(907) 555-1234', 'downtownanchorage@brickmart.com', 'mgr_124', '2018-07-01', 3800.0, true, 61.2176, -149.8951, '10'),
('125', 'BrickMart Midtown Anchorage', '1200 W Northern Lights Blvd', 'Anchorage', 'AK', '99503', 'USA', '(907) 555-2345', 'midtownanchorage@brickmart.com', 'mgr_125', '2019-05-15', 4200.0, true, 61.195, -149.9002, '10'),
('126', 'BrickMart South Anchorage', '11409 Business Blvd', 'Anchorage', 'AK', '99515', 'USA', '(907) 555-3456', 'southanc@brickmart.com', 'mgr_126', '2017-09-01', 3600.0, false, 61.1181, -149.878, '10'),
('127', 'BrickMart Eagle River', '12001 Business Blvd', 'Anchorage', 'AK', '99577', 'USA', '(907) 555-4567', 'eagleriver@brickmart.com', 'mgr_127', '2020-03-01', 3200.0, false, 61.3293, -149.568, '10'),
('128', 'BrickMart Spenard', '1000 W Northern Lights Blvd', 'Anchorage', 'AK', '99503', 'USA', '(907) 555-5678', 'spenard@brickmart.com', 'mgr_128', '2018-11-15', 3400.0, true, 61.195, -149.9002, '10'),

-- Los Angeles Area Stores
('138', 'BrickMart Downtown LA', '350 S Grand Ave', 'Los Angeles', 'CA', '90071', 'USA', '(213) 555-1234', 'dtla@brickmart.com', 'mgr_138', '2018-06-15', 4200.0, true, 34.0522, -118.2437, '6'),
('139', 'BrickMart Hollywood', '6380 Hollywood Blvd', 'Los Angeles', 'CA', '90028', 'USA', '(323) 555-2345', 'hollywood@brickmart.com', 'mgr_139', '2019-03-01', 3500.0, true, 34.1016, -118.3267, '6'),
('140', 'BrickMart Venice Beach', '1800 Ocean Front Walk', 'Los Angeles', 'CA', '90291', 'USA', '(310) 555-3456', 'venice@brickmart.com', 'mgr_140', '2017-08-01', 2800.0, false, 33.985, -118.4695, '6'),
('141', 'BrickMart Silver Lake', '2800 Sunset Blvd', 'Los Angeles', 'CA', '90026', 'USA', '(323) 555-4567', 'silverlake@brickmart.com', 'mgr_141', '2020-02-15', 3200.0, false, 34.0775, -118.2695, '6'),
('142', 'BrickMart Echo Park', '1500 Echo Park Ave', 'Los Angeles', 'CA', '90026', 'USA', '(323) 555-5678', 'echopark@brickmart.com', 'mgr_142', '2019-07-01', 2900.0, true, 34.0782, -118.2606, '6'),
('143', 'BrickMart Los Feliz', '1800 N Vermont Ave', 'Los Angeles', 'CA', '90027', 'USA', '(323) 555-6789', 'losfeliz@brickmart.com', 'mgr_143', '2018-09-15', 3400.0, false, 34.1044, -118.2919, '6'),
('144', 'BrickMart Koreatown', '3500 W 6th St', 'Los Angeles', 'CA', '90020', 'USA', '(213) 555-7890', 'ktown@brickmart.com', 'mgr_144', '2017-11-01', 3800.0, true, 34.0628, -118.3002, '6'),
('145', 'BrickMart West LA', '11666 Olympic Blvd', 'Los Angeles', 'CA', '90064', 'USA', '(310) 555-8901', 'westla@brickmart.com', 'mgr_145', '2020-01-15', 4000.0, false, 34.0379, -118.442, '6'),
('146', 'BrickMart Studio City', '12345 Ventura Blvd', 'Los Angeles', 'CA', '91604', 'USA', '(818) 555-9012', 'studiocity@brickmart.com', 'mgr_146', '2019-05-01', 3600.0, true, 34.1395, -118.3968, '6'),
('147', 'BrickMart Culver City', '9800 Washington Blvd', 'Los Angeles', 'CA', '90232', 'USA', '(310) 555-0123', 'culvercity@brickmart.com', 'mgr_147', '2018-04-15', 3300.0, false, 34.0211, -118.3965, '6'),

-- San Diego Area Stores
('148', 'BrickMart Gaslamp Quarter', '614 5th Ave', 'San Diego', 'CA', '92101', 'USA', '(619) 555-1234', 'gaslamp@brickmart.com', 'mgr_148', '2019-08-01', 3500.0, true, 32.7157, -117.1611, '6'),
('149', 'BrickMart Pacific Beach', '4516 Mission Blvd', 'San Diego', 'CA', '92109', 'USA', '(619) 555-2345', 'pacificbeach@brickmart.com', 'mgr_149', '2018-07-15', 3200.0, false, 32.7972, -117.2546, '6'),
('150', 'BrickMart La Jolla', '7514 Girard Ave', 'San Diego', 'CA', '92037', 'USA', '(858) 555-3456', 'lajolla@brickmart.com', 'mgr_150', '2017-12-01', 3800.0, true, 32.8473, -117.2742, '6'),
('151', 'BrickMart North Park', '3000 University Ave', 'San Diego', 'CA', '92104', 'USA', '(619) 555-4567', 'northpark@brickmart.com', 'mgr_151', '2020-03-15', 2900.0, false, 32.7483, -117.1295, '6'),
('152', 'BrickMart Little Italy SD', '1735 India St', 'San Diego', 'CA', '92101', 'USA', '(619) 555-5678', 'littleitaly@brickmart.com', 'mgr_152', '2019-06-01', 3400.0, true, 32.7223, -117.1687, '6'); 