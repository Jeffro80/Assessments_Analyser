# Overview

The Assessments Analyser App maintains master results and completions files and 
prepares reports on the completion of Assessments and Modules.

## Inputs

The app takes in csv files containing raw assessment data to be analysed and master
results files to be updated.

## Outputs

The app outputs CSV files for Master files and XLS files for reports.

## Version

Version Number 0.530  
App last updated 8 November 2018  
Readme last updated 8 November 2018

# Operation

- Place the required, updated data files into the same directory as the app file
- Run the Assessments_Analyser.py file from within Spyder or from the command
line
- Select the desired function from the menu
- Provide the names for any required files or press enter to open the Open file 
dialog.

# Functions

## Analyse Module

Perform analysis on the completion of a specific module within a course. Outputs
a file with the number of students completing the module each month, and another
file with the Student ID, Name, Email and month completed for the required module.

## Create Master Completion File

Creates a Master Completion file for a course. This file tracks the completion
status for each student for each assessment, stating the month and
year the assessment was completed. If it was transferred, transferred is listed,
and if it was not successfully completed it is left blank.

### Required Files

- Master Completions Headings File

## Create Master Results File

Creates a Master Results file for a course. This file tracks the completion
status for each student for each assessment. Each competent assessment has 
'Competent' in the Assessment column and the date (DD/MM/YYYY) in the Date column
on which the assessment was marked competent.

### Required Files

- Master Results Headings File

## Identify Expired Students At Least X% Completion

Identifies expired students that have at least the passed % of course completed and
have not had their entry on the Assessments_<Course_Code> tab of the Enrolments Google
Sheet updated. Graduated students are removed from the output.

### Required Files

- Analysis File
- Assessments Download File
- Graduation Dates File

### Notes

% figures in file names for extracted students are not always correct. E.g. .29 will
be saved as '29%' due to rounding of floats.

## Identify Expired Students 0% Completion

Identifies expired students that have 0% of course completed and have not had their
entry on the Assessments_<Course_Code> tab of the Enrolments Google Sheet updated.

### Required Files

- Analysis File
- Assessments Download File

## Perform Analysis

Performs a range of analysis on the completion of assessments.

### Required Files

- Assessment Names File
- Enrolment Data File
- Enrolment Data Headings File
- Graduation Dates File
- Graduation Dates Headings File
- Master Completion File
- Master Completion Headings File
- Master Results File
- Master Results Headings File
- Module Names File
- Modules File
- Months (Short) File
- Pacific Island Nations File
- Student Data File
- Student Data Headings File

## Update Master Completion File

Updates a Master Completion File with the assessments that were completed during
the month being processed.

### Required Files

- Assessment Data File
- Assessment Data Headings File
- Assessment Names File
- Assessment Scores
- Course Codes File
- Duplicate Names File
- Enrolment IDs File
- Master Completion File
- Master Completion Headings File

## Update Master Results File

Updates the Master Results File with the assessments that were completed during
the month being processed and the date on which they were completed.

### Required Files

- Assessment Data File
- Assessment Data Headings File
- Assessment Names File
- Assessment Scores
- Course Codes File
- Duplicate Names File
- Enrolment IDs File
- Master Results File
- Master Results Headings File

# Files used

## Analysis File

### File Name

Analysis_<Course_Code>.csv  
e.g. Analysis_ADV.csv

### Contents

Analysis file for the course.

### Structure

CSV file with each column found in the Analysis output file from the Perform Analysis
function of the app.

### Source

Output from Perform Analysis function of the app.

### Notes

The file needs to be updated before use (by running analysis on the student assessment
data).

## Assessment Data File

### File Name

\<CoursePK>\_\<Month>\_\<YY>.csv   
e.g. ADV-PT-003_July_18.csv

### Contents

Raw assessments data for a specific course for a specific month.

### Structure

CSV file with the following columns: Date and Time, Name, Grade item,
Original grade, Revised grade, Grader, Source, Overridden, Locked,
Excluded from calculations, Feedback text.

### Source

Grade history report from the Learning Platform for the specific course and
month.

## Assessment Data Headings File

### File Name

Assessment_Data_Headings.txt

### Contents

Column headings for the Assessments Data exported from the Learning Platform,
with EnrolmentID,StudentID,Course appended to the start of the file.

### Structure

Text file with following items, all on one line:   
EnrolmentID,StudentID,Course,Date and time,Name,Grade item,Original grade,
Revised grade,Grader,Source,Overridden,Locked,Excluded from calculations,
Feedback text

### Source

Created when the course was first set up.

### Notes

When a new course is created, check that the raw assessments data export from the
Learning Platform still matches this format. If the column headings differ, a new
Assessment_Data_Headings file will need to be created and a new process developed.

## Assessment Downloads File

### File Name

Assessment_Downloads_<Course_Code>.csv  
e.g. Assessment_Downloads_ADV.csv

### Contents

Data contained on the Assessments_<Course_Code> tab of the Enrolments Google Sheet.

### Structure

CSV file with the following columns: EnrolmentPK, StudentPK, NameGiven, NameSurname,
CoursePK, Assessments Downloaded, Assessments File Updated.

### Source

Assessments_<Course_Code> tab of the Enrolments Google Sheet.

## Assessment Names File

### File Name

Assessment_Names_<Course_Code>.txt where <Course_Code> is the base code for the
course, e.g. ADV.

### Contents

Name of each assessment in the course.

### Structure

TXT file with the name of each assessment in the course listed in one line, comma
separated.

### Source

Course setup.

## Assessment Scores

### File Name

Scores_<Course_Code>.txt where <Course_Code> is the base code for the course, e.g.
ADV.

### Contents

Minimum passing score for each assessment.

### Structure

TXT file with each assessment score separated by commas, on one line. Scores are
listed in order they appear in the course.

### Source

Course setup.

## Course Codes File

### File Name

Course_codes.txt

### Contents

Base course codes for each course in the Student Database, e.g. ADV.

### Structure

TXT file with base code for each course on one line, separated by commas.

### Source

Courses table of the Student Database.

## Duplicate Names File

### File Name

Duplicate_Names_<CoursePK>.txt where <Course_Code> is the base code for the
course, e.g. ADV.

### Contents

Student names that are duplicated in the course (separate students).

### Structure

TXT file with duplicated student names on one line, separated by commas.

### Source

qryEnrolments Query in the Student Database (duplicates only).

## Enrolment Data File

### File Name

enrolment_data.csv

### Contents

Enrolment data for each student.

### Structure

CSV file with the following column headings:
EnrolmentPK, TutorFK, StartDate, ExpiryDate, Status

### Source

qryEnrolmentAnalysis in the Student Database.

## Enrolment Data Headings File

### File Name

Enrolment_Data_Headings.txt

### Contents

Column headings for Enrolment Data.

### Structure

TXT file with the following on one line:
EnrolmentID,TutorFK,StartDate,ExpiryDate,Status

### Source

qryEnrolmentsAnalysis in the Student Database (extract column headings).

## Enrolment IDs File

### File Name

Enrolment_IDs_<CoursePK>.csv where <Course_Code> is the base code for the
course, e.g. ADV.

### Contents

Enrolment IDs and details for students in the base course code.

### Structure

CSV file with the columns EnrolmentPK, StudentPK, CoursePK, Name

### Source

qryEnrolments Query in the Student Database. Can be filtered prior to exporting
if only a specific course is desired.

### Notes

File needs to be updated manually using unknown_names.txt for students that have
different names between the Learning Platform and the Student Database. Use
EnrolmentID to find students listed in unknown_names.txt.

## Graduation Dates File

### File Name

graduation_dates.csv

### Contents

Graduation Date for each EnrolmentID.

### Structure

CSV file with EnrolmentFK and GraduationDate columns.

### Source

qryGraduationDates in the Student Database.

### Notes

Make sure the GraduationDate column is in the format DD/MM/YYYY.

## Graduation Dates Headings File

### File Name

Graduation_Dates_Headings.txt

### Contents

Each column heading for the Graduation Dates file.

### Structure

TXT file with a single line holding the name of each column, separated by commas.

### Source

qryGraduationDates in the Student Database (take the column headings).

## Master Completion File

### File Name

Master_Completion_<CoursePK>.csv where <Course_Code> is the base code for the
course, e.g. ADV.

### Contents

Completion status of each assessment in the course, for each student. Each
assessment can have either a date in the format MMM-YY if the assessment is
Competent, Transferred if the assessment was transferred, or blank if the
assessment has not been marked Competent.

### Structure

CSV file with EnrolmentID,StudentID,Name,Course and then each assessment in the
course. 

### Source

Created when base course set up.

## Master Completions Headings File

### File Name

Master_Completion_Headings_<Course_Code>.txt where <Course_Code> is the base code
e.g. ADV.

### Contents

Headings for the Master Completion file (first four columns and a column for
each assessment).

### Structure

Text file with one line of text. First four items are the following words: 
EnrolmentID,StudentID,Name,Course   
These four words are followed by the name of each assessment, in the order that
they appear in the course. There should be no comma at the end of the last
assessment.

### Source

Create using the assessment names in the course being set up.

## Master Results File

### File Name

Master_Results_<Course_Code>.csv where <Course_Code> is the base code e.g. ADV.

### Contents

Grade status of each assessment in the course, for each student. Assessments 
marked Competent have Competent listed in their Grade column and the date that
they were marked Competent listed in the Date column, in the format DD/MM/YYYY.
If an assessment has not been marked Competent, the Grade and Date columns are
left empty for the assessment.

### Structure

CSV file with EnrolmentID,StudentID,Name,Course and then each assessment in the
course (Grade column and Date column for each).

### Source

Created when base course set up.

## Master Results Headings File

### File Name

Master_Results_Headings_<Course_Code>.txt where <Course_Code> is the base code
e.g. ADV.

### Contents

Headings for the Master Results file (first four columns, a column for
each assessment and a column for each assessment's completion date).

### Structure

Text file with one line of text. First four items are the following words: 
EnrolmentID,StudentID,Name,Course   
These four words are followed by the code for each assessment (format M0T1Grade)
and a date column for the assessment (format M0T1Date).

### Source

Headings can be exported from the Results table of the Student Database.

## Module Names File

### File Name

Module_Names_<Course_Code>.txt where <Course_Code> is the base code e.g. ADV.

### Contents

Name of each module in the course.

### Structure

TXT file with each module listed on one line, separated by commas.

### Source

Base course set up.

## Modules File

### File Name

Modules_<CoursePK>.csv where <Course_Code> is the base code e.g. ADV.

### Contents

Each module and each assessment required to complete that module.

### Structure

CSV file where the first column holds the name of each Module. Subsequent columns
hold the name of each Assignment. Heading row is Module, Assignment 1,
Assignment 2, ... Assignment n (highest assignment number for a module in the
course.

### Source

Base course setup.

## Months (Short) File

### File Name

months_short.txt

### Contents

Months in the format MMM-YY.

### Structure

TXT file with each month listed on one line, separated by commas.

### Source

Created when app was created and updated when necessary.

### Notes

File currently covers months up to December 2023.

## Pacific Island Nations File

### File Name

pacific_island_nations.txt

### Contents

Each Pacific Island nation.

### Structure

TXT file with each Pacific Island nation listed in a single line, separated by
commas with no spaces after the comma.

### Source

Created at app set up and updated as required.

## Student Data File

### File Name

student_data.csv

### Contents

Enrolment details for students including Gender, Date of Birth, Ethnicity and
Employment.

### Structure

CSV file with the following columns: StudentPK, GEnder, DateOfBirth, Ethnicity,
Employment.

### Source

qryStudentAnalysis in the Student Database.

## Student Data Headings File

### File Name

Student_Data_Headings.txt

### Contents

Column headings for Student Data file.

### Structure

TXT file with following entries on one line: 
StudentID,Gender,DateOfBirth,Ethnicity,Employment

### Source

qryStudentAnalysis in the Student Database (extract headings).

### Notes

Should remain consistent but may need updating if there are system changes.

## Student Info File

### File Name

student_info.csv

### Contents

Student ID, Name (First + Last) and Email for each student in the Student
Database.

### Structure

CSV file with StudentPK, Name and Email columns.

### Source

qryStudentFullNames query in the Student Database.

# Dependencies

The following third-party libraries are imported and therefore are required for
the app to run:

- admintools from custtools
- databasetools from custtools
- datetools from custtools
- filetools from custtools

# Development

## Known bugs

- Won't filter out Course Total entry if it also has 'transferred' in its feedback
text.
- % figures in file names for extracted students are not always correct. E.g. .29 will
be saved as '29%' due to rounding of floats.

## Items to fix


## Current development step

- Additional functions for assessments downloads
- Analysis function: Add filtering of sample
- Analysis function: Add specific courses to process_filter_option()

## Required development steps

- Thorough testing of find_transferred.
- Update num_ass_col change so that it takes a list of assessments and checks the
status of each of these columns for computing total.
- Repeat previous for module completion.
- Order the module completion student output on module column (date order not
alphabetical).
- Coding of process_course_filter for specific course.

## Future additions

- Load list of transferred out students and use to remove from unknown print out.
- Process duplicated student records before saving: remove non-passing grades.
- Determine how to deal with students that have transferred - code on Master.
- Add a filter option: inclusion of Transferred students in analysis.
- Option to quit when creating a master file.
- Use list of applied filters to manage which filters can be applied.
- Add filter option for calculating age at enrolment or today().
- Create a new column called enrol_age and use this for filtering of results.
- Add filtering on multiple courses / CPDs.
- Add specific details to current filters used e.g. number of days.
- Add user input for course (specific course).
- Add user input for ethnicity (specific ethnicity).
- Add non- filters, e.g. non-maori.
- Add filtering on multiple ethnicities.
- Add filter on specific tutor.
- Add filter on multiple tutors.
- Add function to check for unknown names in assessment data before processing.
- Add function to identify students that have completed 0 < x < 50%.
- Add function to identify graduated students.
- Add progress completion to analysis app (e.g. adding columns).