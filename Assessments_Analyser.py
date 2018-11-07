# Assessment Analyser
# Version 0.530 7 November 2018
# Created by Jeff Mitchell
# Prepares reports on completion of Assessments and Modules


import copy
import custtools.admintools as ad
import custtools.databasetools as db
import custtools.datetools as da
import custtools.filetools as ft
import numpy as np
import os
import pandas as pd
import re
import sys


def add_filter_check(filters):
    """Check if user wants to add a filter.
    
    Args:
        filters (int): Number of filters currently applied. Used to govern the
        terminology used in output to user ('a' or 'another').
    
    Returns:
        True if want to add a filter.
        False if do not wish to add a filter.
    """
    word = 'a'
    if filters > 0:
        word = 'another'
    while True:
        response = input('\nDo you wish to add {} filter to the data? y/n or '
                         'enter quit to exit. (y/n): '.format(word))
        if response.lower() == 'y':
            return True
        elif response.lower() == 'n':
            return False
        elif response.lower() == 'quit':
            print('\nThe program will now exit. No analysis was performed.')
            sys.exit()
        else:
            print('\nThat is not a valid entry! Please enter either y or n.')
            continue


def add_module_cols(assess_data_df, modules_dict, month_order, keep=True):
    """Add a column for each module to the dataframe and populate.
    
    Takes the list of keys from the modules_dict and adds each as a column to
    the assessment dataframe. In the process each column is updated by checking
    if the student has completed each of the required assessments.
    
    Args:
        assess_data_df (dataframe): Assessment dataframe.
        moddules_dict (dict): Modules and required assessments.
        month_order (list): List with months placed in order.
        keep (bool): True or False for keeping transferred assessments within
        analysis
             - True and transferred assessments still count
             - False and any transferred assessment will result in the module
             being listed as 'Transferred'
    
    Returns:
        assess_data_df (dataframe): Updated with module columns.
    """
    # Add module keys to headings list
    modules = list(modules_dict.keys())
    # Add each module as a column and populate
    for module in modules:
        # Add module column
        assess_data_df[module] = assess_data_df.apply(lambda row: '', axis=1)
        # Populate module column
        assess_data_df[module] = assess_data_df.apply(
                update_module_completion, args=(module, modules_dict,
                                                month_order,keep,), axis=1)
    return assess_data_df


def add_num_ass_comp(assess_data_df, assessments):
    """Add a column for number of assessments completed and populate.
    
    Adds a column to the dataframe for the Number of assessments completed.
    Column is populated by counting the number of columns in the row that have
    a completed assessment (column = TRUE). Column is returned with the number
    of completed assessments.
    
    Args:
        assess_data_df (dataframe): Assessment data for students.
        assessments (list): Assessment column headings (assessment names).
        
    Returns:
        assess_data_df (dataframe) Updated with Completed_Assessments column.
    """
    # Add column for num
    assess_data_df['Completed_Assessments'] = assess_data_df.apply(
            lambda row: 0, axis=1)
    # Populate the column
    assess_data_df['Completed_Assessments'] =  assess_data_df.apply(
            update_num_ass_col, args=(assessments,), axis=1)
    return assess_data_df


def add_num_mod_comp(assess_data_df, modules):
    """Add a column for number of modules completed and populate.
    
    Adds a column to the dataframe for the Number of modules completed.
    Column is populated by counting the number of columns in the row that have
    a completed module (column = TRUE). Column is returned with the number
    of completed modules.
    
    Args:
        assess_data_df (dataframe): Assessment data for students.
        modules (list): Module column headings (module names).
        
    Returns:
        assess_data_df (dataframe) Updated with Completed_Modules column.
    """
    # Add column for num
    assess_data_df['Completed_Modules'] = assess_data_df.apply(
            lambda row: 0, axis=1)
    # Populate the column
    assess_data_df['Completed_Modules'] =  assess_data_df.apply(
            update_num_ass_col, args=(modules,), axis=1)
    return assess_data_df


def add_percent_comp(assess_data_df, total):
    """Add a column for percentage completed and populate.
    
    Adds a column to the dataframe for the Percentage of assessments completed.
    Column is populated by dividing the number of completed assessments by the
    total number of assessments. Column is returned with the percentage of
    completed assessments.
    
    Args:
        assess_data_df (dataframe): Assessment data for students.
        total (int): Total number of assessments in course.
        
    Returns:
        assess_data_df (dataframe) Updated with Completion_Percent column.
    """
    # Add column for num
    assess_data_df['Completion_Percent'] = assess_data_df.apply(
            lambda row: 0, axis=1)
    # Populate the column
    assess_data_df['Completion_Percent'] =  assess_data_df[
            'Completed_Assessments'].apply(update_perc_comp_col, args=(total,))
    return assess_data_df


def analyse_module():
    """Analyse completion of a specific module.
    
    Determines the number of students per month that have completed the
    specified module and returns the email address of each student. Students
    that have had one or more assessments transferred are excluded from the
    analysis.    
    """
    warnings = ['\nProcessing Module Analysis Data Warnings:\n']
    warnings_to_process = False
    print('\nProcessing Module Analysis Data.')
    # Confirm the required files are in place
    required_files = ['Modules File', 'Module Names File',
                      'Months (Short) File',
                      'Student Info File', 'Master Completions File',
                      'Master Completions Headings File']
    ad.confirm_files('Process Module Analysis Data', required_files)
    # Get course code
    course_code = get_course_code()
    # Load master file for course
    print('\nLoading {}...'.format('Master_Completion_{}.csv'.format(
            course_code)))
    master_data = ft.load_csv('Master_Completion_{}.csv'.format(course_code))
    print('Loaded {}.'.format('Master_Completion_{}.csv'.format(course_code)))
    # Load Master headings file
    print('\nLoading {}...'.format('Master_Completion_Headings_{}'.format
          (course_code)))
    master_headings = ft.load_headings('Master_Completion_Headings_{}'.format
                                       (course_code), 'e')
    print('Loaded {}.'.format('Master_Completion_Headings_{}'.format
          (course_code)))
    # Get non-assessment headings (note length hard-coded)
    # Gets EnrolmentID, StudentID, Name, Course
    start_headings = master_headings[:4]
    # Load student data
    print('\nLoading {}...'.format('Student Info File'))
    student_info = ft.load_csv('student_info', 'e')
    print('Loaded {}.'.format('Student Info File'))
    # Create DataFrame for Student Info
    s_id_col = 'StudentID'
    name_col = 'Name'
    email_col = 'Email'
    s_headings = [s_id_col, name_col, email_col]
    student_info_df = pd.DataFrame(data = student_info, columns = s_headings)
    # Drop name column
    updated_student_headings = [s_id_col, email_col]
    student_info_df = student_info_df[updated_student_headings]
    # Load months order file
    print('\nLoading {}...'.format('Months (Short) File'))
    month_order = ft.load_headings('months_short', 'e')
    print('Loaded {}.'.format('Months (Short) File'))
    # Load module names file
    print('\nLoading {}...'.format('Module_Names_{}'.format(course_code)))
    module_names = ft.load_headings('Module_Names_{}'.format(course_code), 'e')
    print('Loaded {}.'.format('Module_Names_{}'.format(course_code)))
    # Load Modules data into a list of lists
    print('\nLoading {}...'.format('Modules_{}.csv'.format(course_code)))
    modules = ft.load_csv('Modules_{}.csv'.format(course_code))
    print('Loaded {}.'.format('Modules_{}.csv'.format(course_code)))
    # Drop entries that are ''
    modules = clean_modules(modules)
    # Get module to process
    module = get_module_name(module_names)
    # print('Selected module is: {}'.format(module))
    # Get module headings
    module_headings = get_module_headings(start_headings,modules, module)
    # print(module_headings)
    # Create a dictionary to hold module assessment names
    module_dict = create_module_dict(modules, module)
    # print(module_dict)
    # Create dataframe for master assessment data
    assess_data_df = pd.DataFrame(data=master_data, columns=master_headings)
    # print(assess_data_df)
    # Drop assessment columns not required
    assess_data_df = assess_data_df[module_headings]
    # print(assess_data_df)
    # Add column for date module completed
    assess_data_df = add_module_cols(assess_data_df, module_dict, month_order,
                                     False)
    # Drop students not completed module or with transferred
    # Convert 'Transferred' to ''
    remove = ['Transferred']
    assess_data_df[module] = assess_data_df[module].apply(ad.convert_to_value,
                  args=(remove, '',))
    # Convert'' to NaN
    remove = [None, '']
    assess_data_df[module] = assess_data_df[module].apply(ad.convert_to_nan,
                  args=(remove,))
    # Drop NaN from module column
    assess_data_df.dropna(subset=[module], inplace=True)
    # Get number of completions per month for the module
    months_grouped = assess_data_df.groupby(module)
    months_count = months_grouped[module].count()
    # Create a dict from months_grouped
    month_completions_dict = months_count.to_dict()
    # Order the dictionary
    ordered_completion_months = ad.create_ordered_list(month_completions_dict,
                                                       month_order)
    # Save output file for month counts
    month_col = 'Month'
    total_col = 'Total'
    headings = [month_col, total_col]
    # Replace spaces with _ in Module name
    module_name = ad.replace_string(module, ' ', '_')
    ft.save_data_csv(ordered_completion_months, headings,
                     '{}_{}_Completion_Counts_'.format(course_code,
                      module_name))
    # Add emails to students
    # Merge dataframes on Student ID columns
    student_info_months_df = pd.merge(assess_data_df, student_info_df,
                                   on='StudentID', how='left')
    # Drop assessment columns
    student_cols = [s_id_col, name_col, email_col, module]
    student_info_months_df = student_info_months_df[student_cols]
    # Save Module Analysis - uncomment if needed for debugging
    '''
    file_name = 'Module_analysis_{}.csv'.format(ft.generate_time_string())
    assess_data_df.to_csv(file_name, index=False)
    '''
    file_name = '{}_{}_Students_{}.csv'.format(course_code, module_name,
                 ft.generate_time_string())
    student_info_months_df.to_csv(file_name, index=False)
    print('\nCompleted student information has been saved to {}'.format
          (file_name))
    ft.process_warning_log(warnings, warnings_to_process)
    
    
def analysis():
    """Analyse data."""
    warnings = ['\nProcessing Analysis Data Warnings:\n']
    warnings_to_process = False
    print('\nProcessing Analysis Data.')
    # Confirm the required files are in place
    required_files = ['Master Completion File',
                      'Master Completion Headings File', 
                      'Master Results File', 'Master Results Headings File',
                      'Modules File', 'Assessment Names File',
                      'Student Data File', 'Enrolment Data Headings File',
                      'Pacific Island Nations File', 'Graduation Dates File',
                      'Graduation Dates Headings File', 'Enrolment Data File',
                      'Months (Short) File', 'Student Data Headings File',
                      'Module Names File']
    ad.confirm_files('Process Analysis Data', required_files)
    # Get course code
    course_code = get_course_code()
    # Load Master Completion file for course
    print('\nLoading {}...'.format('Master_Completion_{}.csv'.format(
            course_code)))
    master_comp_data = ft.load_csv('Master_Completion_{}.csv'.format(
            course_code))
    print('Loaded {}.'.format('Master_Completion_{}.csv'.format(course_code)))
    # Load Master Completion Headings file
    print('\nLoading {}...'.format('Master_Completion_Headings_{}'.format(
            course_code)))
    master_comp_headings = ft.load_headings('Master_Completion_Headings_{}'
                                            .format(course_code), 'e')
    print('Loaded {}.'.format('Master_Completion_Headings_{}'.format(
            course_code)))
    # Load Master Results file for course
    print('\nLoading {}...'.format('Master_Results_{}.csv'.format(
            course_code)))
    master_res_data = ft.load_csv('Master_Results_{}.csv'.format(course_code))
    print('Loaded {}.'.format('Master_Results_{}.csv'.format(course_code)))
    # Load Master Results Headings file
    print('\nLoading {}...'.format('Master_Results_Headings_{}'.format(
            course_code)))
    master_res_headings = ft.load_headings('Master_Results_Headings_{}'.format(
            course_code), 'e')
    print('Loaded {}.'.format('Master_Results_Headings_{}'.format(
            course_code)))
    # Load months order file
    print('\nLoading {}...'.format('Months (Short) File'))
    month_order = ft.load_headings('months_short', 'e')
    print('Loaded {}.'.format('Months (Short) File'))
    # Load assessment names file
    print('\nLoading {}...'.format('Assessment_Names_{}'.format(course_code)))
    assessment_names = ft.load_headings('Assessment_Names_{}'.format(
            course_code), 'e')
    print('Loaded {}.'.format('Assessment_Names_{}'.format(course_code)))
    num_assessments = len(assessment_names)
    # Load module names file
    print('\nLoading {}...'.format('Module_Names_{}'.format(course_code)))
    module_names = ft.load_headings('Module_Names_{}'.format(course_code), 'e')
    print('Loaded {}.'.format('Module_Names_{}'.format(course_code)))
    # Load enrolment_data file
    print('\nLoading {}...'.format('Enrolment Data File'))
    enrolment_data = ft.load_csv('enrolment_data', 'e')
    print('Loaded {}.'.format('Enrolment Data File'))
    # Load Enrolment Data Headings file
    print('\nLoading {}...'.format('Enrolment Data Headings File'))
    enrol_data_headings = ft.load_headings('Enrolment_Data_Headings', 'e')
    print('Loaded {}.'.format('Enrolment Data Headings File'))
    # Load Student Data
    print('\nLoading {}...'.format('Student Data File'))
    student_data = ft.load_csv('student_data', 'e')
    print('Loaded {}.'.format('Student Data File'))
    # Load Student Data Headings file
    print('\nLoading {}...'.format('Student Data Headings File'))
    student_data_headings = ft.load_headings('Student_Data_Headings', 'e')
    print('Loaded {}.'.format('Student Data Headings File'))
    # Load Graduation Dates Data
    print('\nLoading {}...'.format('Graduation Dates Data'))
    grad_dates_data = ft.load_csv('graduation_dates', 'e')
    print('Loaded {}.'.format('Graduation Dates Data'))
    # Load Graduation Dates Data Headings file
    print('\nLoading {}...'.format('Graduation Dates Headings File'))
    grad_dates_headings = ft.load_headings('Graduation_Dates_Headings',
                                                 'e')
    print('Loaded {}.'.format('Graduation Dates Headings File'))
    # Load Pacific Island Nations File
    print('\nLoading {}...'.format('Pacific Island Nations File'))
    island_nations = ft.load_headings('pacific_island_nations.txt')
    print('Loaded {}.'.format('Pacific Island Nations File'))
    # Create dataframe for Master Completion data
    comp_data_df = pd.DataFrame(data=master_comp_data,
                                  columns=master_comp_headings)
    # Create dataframe for enrolment data
    enrol_data_df = pd.DataFrame(data=enrolment_data,
                                 columns=enrol_data_headings)
    # Create dataframe for student data
    student_data_df = pd.DataFrame(data=student_data,
                                 columns=student_data_headings)
    # Create dataframe for graduation data
    grad_data_df = pd.DataFrame(data=grad_dates_data,
                                columns=grad_dates_headings)
    # Merge comp_data_df with Enrolments Table data
    comp_data_df = pd.merge(comp_data_df, enrol_data_df, on='EnrolmentID',
                         how='left')
    # Merge comp_data_df with Student Table data
    comp_data_df = pd.merge(comp_data_df, student_data_df, on='StudentID',
                         how='left')
    # Merge comp_data_df with Graduate Dates data
    comp_data_df = pd.merge(comp_data_df, grad_data_df, on='EnrolmentID',
                         how='left')
    # Add column for Pacific Island status to Master Completion
    comp_data_df['Pacific'] = comp_data_df['Ethnicity'].apply(get_pacific,
                args=(island_nations,))
    # Add column for Age at enrolment to Master Completion and populate
    comp_data_df['Age'] = comp_data_df.apply(lambda x:
        get_age(x['DateOfBirth'], x['StartDate']), axis=1)
    # Add column for enrolment length to Master Completion
    comp_data_df['EnrolLength'] = comp_data_df.apply(lambda x: get_e_length(
            x['Status'], x['StartDate'], x['ExpiryDate'], x['GraduationDate']
            ),axis=1)
    # Temp save
    '''
    file_name = 'Check_merge_comp{}.csv'.format(ft.generate_time_string())
    comp_data_df.to_csv(file_name, index=False)
    '''
    # Create dataframe for Master Results data
    res_data_df = pd.DataFrame(data=master_res_data,
                                  columns=master_res_headings)
    # Merge res_data_df with Enrolments Table data
    res_data_df = pd.merge(res_data_df, enrol_data_df, on='EnrolmentID',
                         how='left')
    # Merge res_data_df with Student Table data
    res_data_df = pd.merge(res_data_df, student_data_df, on='StudentID',
                         how='left')
    # Merge res_data_df with Graduate Dates data
    res_data_df = pd.merge(res_data_df, grad_data_df, on='EnrolmentID',
                         how='left')
    # Add column for Pacific Island status to Master Results
    res_data_df['Pacific'] = res_data_df['Ethnicity'].apply(get_pacific,
                args=(island_nations,))
    # Add column for Age at enrolment to Master Results and populate
    res_data_df['Age'] = res_data_df.apply(lambda x: get_age(x['DateOfBirth'],
               x['StartDate']), axis=1)
    # Add column for enrolment length to Master Results
    res_data_df['EnrolLength'] = res_data_df.apply(lambda x: get_e_length(
            x['Status'], x['StartDate'], x['ExpiryDate'], x['GraduationDate']
            ),axis=1)
    # Temp save
    '''
    file_name = 'Check_merge_res{}.csv'.format(ft.generate_time_string())
    res_data_df.to_csv(file_name, index=False)
    '''
    # Load Modules data into a list of lists
    print('\nLoading {}...'.format('Modules_{}.csv'.format(course_code)))
    modules = ft.load_csv('Modules_{}.csv'.format(course_code))
    print('Loaded {}.'.format('Modules_{}.csv'.format(course_code)))
    # Drop entries that are ''
    modules = clean_modules(modules)
    # Create a dictionary to hold modules
    modules_dict = create_modules_dict(modules)
    # ad.debug_dict(modules_dict)
    # Filter data if required
    comp_data_df, res_data_df = filtering(comp_data_df, res_data_df)
    # Add columns to assessment data for each module
    comp_data_df = add_module_cols(comp_data_df, modules_dict, month_order)
    # Add Number of assessments completed column
    comp_data_df = add_num_ass_comp(comp_data_df, assessment_names)
    # Add module completion columns
    comp_data_df = add_num_mod_comp(comp_data_df, module_names)
    # Add % of course completed column
    comp_data_df = add_percent_comp(comp_data_df, num_assessments)
    # Temp saving
    '''
    file_name = 'Master_res_check_{}.csv'.format(ft.generate_time_string())
    res_data_df.to_csv(file_name, index=False)
    '''
    # Save Analysis file
    file_name = 'Analysis_{}_{}.csv'.format(course_code,
                          ft.generate_time_string())
    comp_data_df.to_csv(file_name, index=False)
    print('\nAnalysis file saved as {}'.format(file_name))
    ft.process_warning_log(warnings, warnings_to_process)


def analysis_message():
    """Display Analysis Menu."""
    # Get number of assessments completed
    # Get % of assessments completed


def apply_age_filter(age, lower, upper):
    """Convert to NaN ages outside of the provided range.
    
    Args:
        age (int): Student age.
        lower (int): Lower boundary of filter.
        upper (int): Upper boundary of filter.
    
    Returns:
       age (int) Original age or NaN if outside of filter range.
    """
    if age in (None, ''):
        return np.nan
    elif age >= lower and age <= upper:
        return age
    else:
        return np.nan
    

def apply_course_filter(course, target, wild_cards=True):
    """Convert to NaN courses not in the target filter.
    
    Args:
        course (str): Student course.
        target (str): Course code or base code to be searched for.
        wild_cards (bool): If True, .+ used either side of course code. Used if
        looking at study type etc. If False, .+ not used, e.g. for searching
        for a specific course.
    
    Returns:
       course (str) Original course or NaN if outside of filter target.
    """
    if wild_cards:
        wild = '.+'
    else:
        wild = ''
    if course in (None, ''):
        return np.nan
    elif re.search('{}{}{}'.format(wild, target, wild), course):
        return course
    else:
        return np.nan


def apply_el_filter_above(enrolment_length, minimum):
    """Convert to NaN enrolment lengths not above or equal to minimum.
    
    Args:
       enrolment_length (int): Length of enrolment.
       minimum (int): Minimum allowed enrolment length.
    
    Returns:
       enrolment_length (int): Original enrolment length or NaN if less than
       minimum.
    """
    if enrolment_length in (None, ''):
        return np.nan
    elif enrolment_length >= minimum:
        return enrolment_length
    else:
        return np.nan


def apply_el_filter_below(enrolment_length, maximum):
    """Convert to NaN enrolment lengths not below or equal to maximum.
    
    Args:
       enrolment_length (int): Length of enrolment.
       maximum (int): Maximum allowed enrolment length.
    
    Returns:
       enrolment_length (int): Original enrolment length or NaN if greater than
       maximum.
    """
    if enrolment_length in (None, ''):
        return np.nan
    elif enrolment_length <= maximum:
        return enrolment_length
    else:
        return np.nan


def apply_el_filter_between(enrolment_length, minimum, maximum):
    """Convert to NaN enrolment lengths not between required range.
    
    Args:
       enrolment_length (int): Length of enrolment.
       minimum (int): Minimum allowed enrolment length.
       maximum (int): Maximum allowed enrolment length.
    
    Returns:
       enrolment_length (int): Original enrolment length or NaN if not in
       allowed range.
    """
    if enrolment_length in (None, ''):
        return np.nan
    elif enrolment_length >= minimum and enrolment_length <= maximum:
        return enrolment_length
    else:
        return np.nan


def apply_filter(value, filter_value, keep=True):
    """Convert to NaN students not matching the filter_value.
    
    Drops students that do not match the filter_value. If keep = False,
    drops students that do match the target_value.
    
    Args:
        value (str): Value for student.
        target_value (str): Value to filter on.
        keep (bool): True then drop non-matching students, False then
        drop matching students.
    
    Returns:
       value (str): Original value or NaN if outside filter.
    """
    if value in (None, ''):
        return np.nan
    # Removing non-matching students
    if keep:
        if value == filter_value:
            return value
        else:
            return np.nan
    # Removing matching students
    else:
        if value == filter_value:
            return np.nan
        else:
            return value


def apply_pacific_filter(pacific, keep=True):
    """Convert to NaN students not of Pacific ethnicity.
    
    Drops students that do not have Yes in Pacific column. If keep = False,
    drops students that are of Pacific ethnicity.
    
    Args:
        pacific (str): Value of Pacific column (Yes, No).
        keep (bool): True then drop non-pacific students, False then drop
        pacific students.
    
    Returns:
       pacific (str): Original Pacific value or NaN if outside filter.
    """
    if pacific in (None, ''):
        return np.nan
    # Removing non-pacific students
    if keep:
        if pacific == 'Yes':
            return pacific
        else:
            return np.nan
    # Removing pacific students
    else:
        if pacific == 'Yes':
            return np.nan
        else:
            return pacific


def check_assesment(completed=True):
    """Report students completed a specific assessment."""
    # Save a report with all of the students that have completed assessment


def check_course_code(course_code, file_type):
    """Checks if a course master file already exists.
    
    Checks if a course master file already exists by attempting to write to a
    file with the course code. If the file is found the user will be asked to
    use a different course code.
    
    Args:
        course_code (str): Supplied course code to use.
        file_type (str): File being checked. From:
             - Completions
             - Results
        
    Returns:
        course_code (str): Confirmed course code to use.
    """
    # Check if file already exists (True means it does)
    confirmed = False
    while not confirmed:
        file_name = 'Master_{}_{}.csv'.format(file_type, course_code)
        file_exists = os.path.isfile(file_name)
        if file_exists:
            print('\nThat Master File already exists! Please enter a different'
                  ' course code.')
            course_code = input('\nWhat is the code for the course? '
                                'Alternatively, type q to quit: ')
            if course_code == 'q':
                print('\nProgram cancelled. Goodbye.')
                sys.exit()
        else:
            print('\nCourse code accepted\n')
            return course_code


def check_df(dataframe):
    """Check if dataframe contains data.
    
    Checks if the dataframe is empty. If it is, the program quits to prevent
    an error. If not, the program continues.
    
    Args:
        dataframe (dataframe): Dataframe to be checked.
    """
    if dataframe.empty:
        print('\nNo data is left to be processed. The program will now exit. '
              'Please check the source files and any output files to check '
              'that there is not an error with the data if this is unexpected'
              '.')
        sys.exit()
    else:
        return


def check_scores(score, grade_item, passing_scores):
    """Return score if passing or nan if not.
    
    Finds the minimum passing score for the grade item in the passing_scores
    dictionary and determines if the provided score is a passing score.
    
    Args:
        score (int): Revised grade for assessment.
        grade_item (str): Assessment task name.
        passing_scores (dict): Minimum passing score for each assessment.
    """
    if score >= passing_scores[grade_item]: # passing score
        return score
    else:
        return np.nan


def clean_modules(modules):
    """Remove empty items from modules list.
    
    Args:
        modules (list): List of module assessments (list of lists).
        
    Returns:
        modules (list): List of module assessments (list of lists) with empty
        items removed.
    """
    # Debugging script - uncomment to check passed modules
    '''
    print('Passed modules:')
    ad.debug_list(modules)
    '''
    for item in modules:
        n = 0
        while n < len(item):
            if item[n] in (None, ''):
                del item[n]
                # Don't increment n due to removal of item
            else:
                n += 1
    # ad.debug_list(modules)
    return modules                


def convert_grade_item(item, grades_dict):
    """Converts a Grade item into the correct heading value.
    
    Finds the Grade item in the grades_dict and returns the equivalent heading
    from the Master Results file. Used to make sure the headings match those
    that are used in the Student Database.
    
    Args:
        item (str): Grade item from assessments data.
        grades_dict (dict): Dictionary with assessments grade item as the key
        and the corresponding heading in the Master Results file as the value.
        
    Returns:
        grade_item (str): The replacement grade item heading.
    """
    return grades_dict[item]


def convert_month(month, month_order):
    """Converts a month into an int for its place in the order of months.
    
    month_order is a dictionary holding each month. Values are an int stating
    the position of the month in the order, oldest first. Function converts
    the passed month to an int that represents its position in month_order.
    Older months will have a lower int value. Months can then be sorted based
    on their int (position in month_order).
    
    Args:
        month (str): Month and Year passed.
        month_order (dict): Keys are month + year combinations and values are
        the position of the month + year combination in month_order.
    """
    return month_order[month]


def convert_scores(scores):
    """Convert list of scores to intergers.
    
    Args:
        scores (list): Raw scores stored as strings.
    
    Returns:
        updated_Scores (list): Each digit is stored as an int.
    """
    updated_scores = []
    for score in scores:
        if score == 'None':
            updated_scores.append(np.nan)
        else:
            converted_score = ad.convert_to_int(score)
            if converted_score:
                updated_scores.append(converted_score) # valid int
            else:
                updated_scores.append(np.nan) # Not a valid int
    return updated_scores


def create_grades_dict(assessments, master_headings):
    """Create dictionary to hold assessment names for results.
    
    Takes the first item in a list and sets as the dictionary key. Each
    further item in the list for that module is added as a value. Values are
    stored as a list of items, each item being one required assessment for that
    module.
    
    Args:
        assessments (list): List of assessment names (raw data).
        master_headings (list): Headings in the Master Results File.
        
    Returns:
        grades_dict (dict): Dictionary with each assessment name as a key and
        the equivalent name in the Master Results File as a value.
    """
    grades_dict = {}
    n = 4 # Skip first four items in master_headings (student data)
    # Each assessment item processed
    for assessment in assessments:
        grades_dict[assessment] = master_headings[n]
        n+=2 # Skip date column and progress to next assessment
    return grades_dict


def create_master_file(file_type):
    """Create a master file for a course.
    
    Creates a Master file for a specific course. 
    
    Args:
        file_type (str): The type of file that is being created.
        Options are from: Completion, Results.    
    """
    warning = '\nProcessing Master {} File Creation Data Warnings:\n'.format(
            file_type)
    warnings = [warning]
    warnings_to_process = False
    print('\nProcessing Master {} File Creation Data.'.format(file_type))
    # Confirm the required files are in place
    required_files = ['Master {} Headings File'.format(file_type)]
    ad.confirm_files('Master {} File'.format(file_type), required_files)
    # Get course code to process
    course_code = input('\nEnter the course code to be used for the new '
                        'Master {} File --> '.format(file_type))
    # Check if course master file already exists - get different code if so
    course_code = check_course_code(course_code, file_type)
    # Get column headings for the Master File
    print('\nLoading {}...'.format('Master_{}_Headings_{}'.format(file_type,
            course_code)))
    assessments = ft.load_headings('Master_{}_Headings_{}'.format(file_type,
            course_code), 'e')
    print('Loaded {}.'.format('Master_{}_Headings_{}'.format(file_type,
            course_code)))
    # Create empty data list
    data = []
    # Save empty masters file
    master_name = 'Master_{}_{}_'.format(file_type, course_code)
    ft.save_list_csv(data, assessments, master_name)
    ft.process_warning_log(warnings, warnings_to_process)


def create_module_dict(modules, target_module):
    """Create dictionary to hold assessment names for one module.
    
    Takes the first item in a list and sets as the dictionary key. Each
    further item in the list for that module is added as a value. Values are
    stored as a list of items, each item being one required assessment for that
    module.
    
    Args:
        modules (list): List of lists with info for each module.
        target_module (str): Module to extract and process
        
    Returns:
        module_dict (dict): Dictionary with each module as a key and each
        assessment required for the module as a value.
    """
    module_dict = {}
    for module in modules:
        if module[0] == target_module:
            module_dict[module[0]] = module[1:]
            return module_dict 


def create_modules_dict(modules):
    """Create dictionary to hold modules and assessments.
    
    Takes the first item in each list and sets as the dictionary key. Each
    further item in the list for that module is added as a value. Values are
    stored as a list of items, each item being one required assessment for that
    module.
    
    Args:
        modules (list): List of lists with info for each module.
        
    Returns:
        module_dict (dict): Dictionary with each module as a key and each
        assessment required for the module as a value.
    """
    module_dict = {}
    for module in modules:
        module_dict[module[0]] = module[1:]
    return module_dict     


def display_avail_filter_groups():
    """Display filter group options."""
    print('\nAvailable filter groups:')
    print('\n1. Age')
    print('2. Course')
    print('3. Enrolment Length')
    print('4. Ethnicity')
    print('5. Gender')
    print('6. Status')    
    print('7. Tutor')
    print('8. No filter (cancel).')


def display_applied_filters(filters):
    """Display filters to be applied.
    
    Args:
        filters (list): Filters applied.
    """
    if not filters:
        print('\nTthere are no filters being applied.')
    else:
        print('\nThe following filters will be applied to the data:\n')
        n = 1 # For updating line number
        for item in filters:
            print('{}. {}'.format(n, item))
            n+=1
    return


def display_current_filters(filters):
    """Display filters currently applied.
    
    Args:
        filters (list): Filters applied.
    """
    if not filters:
        print('\nCurrently there are no filters applied.')
    else:
        print('\nThe following filters are currently applied to the data:\n')
        n = 1 # For updating line number
        for item in filters:
            print('{}. {}'.format(n, item))
            n+=1
    return


def extract_day_month_year(date_data):
    """Extract day, month and year from date time data.
    
    Finds the day, month and year and returns as a string.
    
    Args:
        date_data (str): Time stame information.
        
    Returns:
        extracted_date (str): Day + Month + Year.
    """
    # Find first space
    first_space = date_data.index(' ')
    # Find second space
    first_slice = date_data[first_space+1:]
    comma = first_slice.index(',')
    extracted_date = first_slice[:comma]
    # Return from the Day number up to the end of the Year
    return extracted_date
    

def extract_month_year(date_data):
    """Extract month and year from date time data.
    
    Finds the month and year and returns as a string.
    
    Args:
        date_data (str): Time stame information.
        
    Returns:
        extracted_date (str): Month + Year.
    """
    # Find first space
    first_space = date_data.index(' ')
    # Find second space
    first_slice = date_data[first_space+1:]
    second_space = first_slice.index(' ')
    # Find next comma
    second_slice = first_slice[second_space+1:]
    comma = second_slice.index(',')
    return second_slice[:comma]


def extract_zero_comp():
    """Return students that have 0% completion for the course.
    
    Finds students with 0% completion that have not been updated in the
    assessments download data file.
    """
    warnings = ['\nProcessing Zero Completion Data Warnings:\n']
    warnings_to_process = False
    print('\nProcessing Zero Completion Data.')
    # Confirm the required files are in place
    required_files = ['Assessment Downloads File', 'Analysis File']
    ad.confirm_files('Process Zero Completion Data', required_files)
    # Get course code
    course_code = get_course_code()
    # Load Assessments Download file
    print('\nLoading {}...'.format('Assessment_Downloads_{}.csv'.format(
            course_code)))
    assess_downloads_data = ft.load_csv('Assessment_Downloads_{}.csv'.format(
            course_code))
    print('Loaded {}.'.format('Assessment_Downloads_{}.csv'.format(
            course_code)))
    # Load Analysis file
    print('\nLoading {}...'.format('Analysis_{}.csv'.format(course_code)))
    analysis_data = ft.load_csv('Analysis_{}.csv'.format(
            course_code))
    print('Loaded {}.'.format('Analysis_{}.csv'.format(
            course_code)))
    # Extract Enrolment IDs from Analysis data into a list
    analysis_ids = ad.extract_list_item(analysis_data, 0)
    # Extract from Assessments Download data students with zero completion
    zero_students = get_zero_students(assess_downloads_data, analysis_ids)
    # Save file
    print('')
    headings = ['EnrolmentPK', 'StudentPK', 'NameGiven', 'NameSurname',
                'CoursePK']
    file_name = 'Zero_students_{}_'.format(course_code)
    ft.save_data_csv(zero_students, headings, file_name)
    ft.process_warning_log(warnings, warnings_to_process)


def filtering(comp_data, res_data):
    """Get and apply filters to data prior to analysis.
    
    Args:
        comp_data (dataframe): Master Completion data.
        res_data (dataframe): Master Results data.
    
    Return:
        filtered_comp_data (dataframe): Filtered Master Completion data.
        filtered_res_data (dataframe): Filtered Master Results data.
    """
    # Make copy of dataframes in case need to revert
    f_comp_data = comp_data.copy()
    f_res_data = res_data.copy()
    # Hold applied filters
    filters = []
    # Present filter group options and get filter
    while True:
        # Display current filters
        display_current_filters(filters)
        # Check if wish to add filter
        if not add_filter_check(len(filters)): # No further filters
            # Check if wish to keep applied filters (if any selected)
            if filters: # One or more filter selected
                if keep_filters():
                    display_applied_filters(filters)
                    return f_comp_data, f_res_data
                else:
                    print('\nNo filters will be applied to the data.')
                    return comp_data, res_data
            # No filters selected
            else:
                print('\nNo filters will be applied to the data.')
                return comp_data, res_data
        # Display available filter groups
        display_avail_filter_groups()
        # Get filter group from user
        filter_group = get_filter_group_option()
        # Get filter from user
        filter_option = get_filter_option(filter_group)
        if not filter_option:
            # Deal with no filter selected
            continue
        # Apply the selected filter
        if filter_group == 'Age':
            # Get lower and upper values
            lower, upper = get_age_range(filter_option)
            # Send to age processing function
            f_comp_data, f_res_data, valid_filter = process_age_filter(
                    lower, upper, f_comp_data, f_res_data)
        elif filter_group == 'Course':
            # Send to course processing function
            f_comp_data, f_res_data, valid_filter = process_course_filter(
                    filter_option, f_comp_data, f_res_data)
        elif filter_group == 'Enrolment Length':
            # Send to enrolment length processing function
            f_comp_data, f_res_data, valid_filter = process_el_filter(
                    filter_option, f_comp_data, f_res_data)
        elif filter_group == 'Ethnicity':
            # Send to ethnicity processing function
            f_comp_data, f_res_data, valid_filter = process_ethnicity_filter(
                    filter_option, f_comp_data, f_res_data)
        elif filter_group == 'Gender':
            # Send to gender processing function
            f_comp_data, f_res_data, valid_filter = process_gender_filter(
                    filter_option, f_comp_data, f_res_data)
        elif filter_group == 'Status':
            # Send to status processing function
            f_comp_data, f_res_data, valid_filter = process_status_filter(
                    filter_option, f_comp_data, f_res_data)
        elif filter_group == 'Tutor':
            # Send to tutor processing function
            f_comp_data, f_res_data, valid_filter = process_tutor_filter(
                    filter_option, f_comp_data, f_res_data)
        if valid_filter:
            # Add filter to the filters list if it was applied
            filters.append(filter_option)
        else:
            print('\n{} resulted in 0 students being returned. For this '
                  'reason the filter will not be used. Data stays the same'
                  '.'.format(filter_option))
    

def filter_options_age_message():
    """Print filtering options based on age."""
    print('\nOptions for filtering (Age):')
    print('\n1. Students aged 0-17')
    print('2. Students aged 18-24')
    print('3. Students aged 25-34')
    print('4. Students aged 35-44')
    print('5. Students aged 45-54')
    print('6. Students aged 55-64')
    print('7. Students aged 65+')
    print('8. Filter on specific age range')
    print('9. No further filter')


def filter_options_course_message():
    """Print filtering options based on course."""
    print('\nOptions for filtering (Course):')
    print('\n1. Online students')
    print('2. Part-time students')
    print('3. CPD students')
    print('4. Specific course students')
    print('5. No further filter')


def filter_options_enrol_length_message():
    """Print filtering options based on enrolment length."""
    print('\nOptions for filtering (Enrolment):')
    print('\n1. No more than x days enrolled')
    print('2. No less than x days enrolled')
    print('3. Between x and y days enrolled')
    print('4. No further filter')


def filter_options_ethnicity_message():
    """Print filtering options based on ethnicity."""
    print('\nOptions for filtering (Ethnicity):')
    print('\n1. Maori students')
    print('2. Pacific Island students')
    print('3. Specific ethnicity students')
    print('4. Filter on multiple ethnicities')
    print('5. No further filter')


def filter_options_gender_message():
    """Print filtering options based on gender."""
    print('\nOptions for filtering (Gender):')
    print('\n1. Female students')
    print('2. Male students')
    print('3. No further filter')


def filter_options_status_message():
    """Print filtering options based on student status."""
    print('\nOptions for filtering (Status):')
    print('\n1. Active students')
    print('2. Non-active students')
    print('3. Expired students')
    print('4. Graduated students')
    print('5. Suspended students')
    print('6. Withdrawn students')
    print('7. Filter on multiple statuses')
    print('8. No further filter')


def filter_options_tutor_message():
    """Print filtering options based on tutor."""
    print('\nOptions for filtering (Tutor):')
    print('\n1. Specific tutor')
    print('2. Filter on multiple tutors')
    print('3. No further filter')


def find_transferred(feedback):
    """Find students that have been transferred.
    
    Examines the feedback text for the student and looks for a note that the
    student has been transferred. If not found, column is set to 'NA' so that
    it can be dropped in a future step.
    
    Args:
        feedback (str): Feedback column for student.
        
    Returns:
        (str): 'Transferred' if transferred, 'NA' if not.
    """
    if feedback in ('', None):
        return np.nan
    elif re.search('.+transfer.+', feedback.lower()):
        return 'Transfer'
    elif re.search('transfer.+', feedback.lower()):
        return 'Transfer'
    elif re.search('.+cross credit.+', feedback.lower()):
        return 'Transfer'
    elif re.search('cross credit.+', feedback.lower()):
        return 'Transfer'
    elif re.search('cross credit', feedback.lower()):
        return 'Transfer'
    elif re.search('transfer', feedback.lower()):
        return 'Transfer'
    else:
        return np.nan


def get_age(date_of_birth, enrolment_date):
    """Return age based on enrolment date.
    
    Args:
        date_of_birth (date): Date of birth in format DD/MM/YYYY.
        enrolment_date (date): Enrolment date in format DD/MM/YYYY.
        
    Returns:
        age (int): Age in years.
    """
    # Skip empty Date of Birth columns
    if date_of_birth in (None, '', np.nan):
        return ''
    # Convert date_of_birth to format YYYY-MM-DD
    updated_date = da.convert_to_datetime(date_of_birth, "%d/%m/%Y")
    # Convert enrolment_date to format YYYY-MM-DD
    updated_enrolment = da.convert_to_datetime(enrolment_date, "%d/%m/%Y")
    age = da.calculate_age(updated_date, updated_enrolment)
    return age


def get_age_filter():
    """Return age filter selection.
    
    Returns:
        selection (str): Age filter selection.
    """
    # List of allowed selections
    allowed = ['1', '2', '3', '4', '5', '6', '7', '8']
    while True:
        # Display age filter options
        filter_options_age_message()
        selection = input('\nPlease enter your selection (number) for the age '
                          'filter you would like to apply. Enter {} if you do '
                          'not wish to add another filter: '.format(
                                  len(allowed)))
        if selection in allowed:
            if selection == '1':
                return 'Students aged 0-17'
            elif selection == '2':
                return 'Students aged 18-24'
            elif selection == '3':
                return 'Students aged 25-34'
            elif selection == '4':
                return 'Students aged 35-44'
            elif selection == '5':
                return 'Students aged 45-54'
            elif selection == '6':
                return 'Students aged 55-64'
            elif selection == '7':
                return 'Students aged 65+'
            elif selection == '8':
                return 'Specified range'
            elif selection == '9':
                return None  
        else:
            print('\nThat is not a valid option. Please select from the '
                  'available options.')


def get_age_range(selection):
    """Return lower and upper values for age range.
    
    If user has specified a custom range, gets the range and then returns
    lower and upper values.
    
    Args:
        selection (str): Range filter selected.
        
    Returns:
        lower (int): Lower value.
        upper (int): Upper value.
    """
    if selection == 'Students aged 0-17':
        return 0, 17
    elif selection == 'Students aged 18-24':
        return 18, 24
    elif selection == 'Students aged 25-34':
        return 25, 34
    elif selection == 'Students aged 35-44':
        return 35, 44
    elif selection == 'Students aged 45-54':
        return 45, 54
    elif selection == 'Students aged 55-64':
        return 55, 64
    elif selection == 'Students aged 65+':
        return 65, 120
    elif selection == 'Specified range':
        lower, upper = get_value_range('age')
        return lower, upper
    

def get_completion_month(months, month_order, order='last'):
    """Return the last completion month.
    
    Checks each item in months and returns the item that is the latest (newest)
    month. If order is passed 'first' it returns the earliest (oldest) month.
    
    Args:
        months (list): Months in which assessments were completed.
        month_order (list): List with each month in order.
        order (str): Order to return.
            last = return the latest date (newest)
            first = return the earliest date (oldest)
    """
    # Debugging script - uncomment to check format of dates
    '''
    print('\nMonths:\n')
    ad.debug_list(months)
    print('\nMonth order:\n')
    ad.debug_list(month_order)
    '''
    # Create dictionary with month values in order
    month_order_dict = ad.create_ordered_dict(month_order)
    # Debugging script - uncomment to check format of dates
    '''
    print('Months list (completed months):')
    ad.debug_list(months)
    print('Months_order_dict:')
    ad.debug_dict(month_order_dict)
    '''
    if months: # make sure there is at least one month passed
        # Set initial latest and earliest months
        latest = month_order_dict[months[0]]
        # print('Latest: {}'.format(latest))
        earliest = month_order_dict[months[0]]
        # print('Earliest: {}'.format(earliest))
        for month in months:
            # Update latest if month is later
            if month_order_dict[month] > latest:
                latest = month_order_dict[month]
            # Update earliest if month is earlier
            elif month_order_dict[month] < earliest:
                earliest = month_order_dict[month]
        # Return desired month
        if order == 'last':
            return month_order[latest]
        elif order == 'first':
            return month_order[earliest]
        else:
            return month_order[latest]
    # Empty string returned if no months passed
    else:
        return ''


def get_course_code():
    """Gets a course code from the user."""
    # Load list of allowed course codes
    valid_codes = ft.load_headings('Course_codes', 'e')
    # Get selection and make sure it is a valid course
    while True:
        code = input('\nWhat is the code for the course? Alternatively, type q'
                     ' to quit: ')
        if code == 'q':
            print('\nProgram cancelled. Goodbye.')
            sys.exit()
        elif code in valid_codes:
            return code
        else:
            print('\nThat is not a valid code. The course must be present in '
                  'the list of valid courses (Course_codes.txt). If it is not'
                  ', please quit and add it.')            


def get_course_filter():
    """Return course filter selection.
    
    Returns:
        selection (str): Course filter selection.
    """
    # List of allowed selections
    allowed = ['1', '2', '3', '4', '5']
    while True:
        # Display course filter options
        filter_options_course_message()
        selection = input('\nPlease enter your selection (number) for the '
                          'course filter you would like to apply. Enter {} if '
                          'you do not wish to add another filter: '.format(
                                  len(allowed)))
        if selection in allowed:
            if selection == '1':
                return 'Online students'
            elif selection == '2':
                return 'Part-time students'
            elif selection == '3':
                return 'CPD students'
            elif selection == '4':
                return 'Specific course students'
            elif selection == '5':
                return None  
        else:
            print('\nThat is not a valid option. Please select from the '
                  'available options.')


def get_enrolment_length_filter():
    """Return enrolment length filter selection.
    
    Returns:
        selection (str): Enrolment length filter selection.
    """
    # List of allowed selections
    allowed = ['1', '2', '3', '4']
    while True:
        # Display enrolment length filter options
        filter_options_enrol_length_message()
        selection = input('\nPlease enter your selection (number) for the '
                          'enrolment length filter you would like to apply. '
                          'Enter {} if you do not wish to add another '
                          'filter: '.format(len(allowed)))
        if selection in allowed:
            if selection == '1':
                return 'No more than x days enrolled'
            elif selection == '2':
                return 'No less than x days enrolled'
            elif selection == '3':
                return 'Between x and y days enrolled'
            elif selection == '4':
                return None  
        else:
            print('\nThat is not a valid option. Please select from the '
                  'available options.')


def get_ethnicity_filter():
    """Return ethnicity filter selection.
    
    Returns:
        selection (str): Ethnicity filter selection.
    """
    # List of allowed selections
    allowed = ['1', '2', '3', '4', '5']
    while True:
        # Display ethnicity filter options
        filter_options_ethnicity_message()
        selection = input('\nPlease enter your selection (number) for the '
                          'ethnicity filter you would like to apply. Enter {} '
                          'if you do not wish to add another filter: '.format(
                                  len(allowed)))
        if selection in allowed:
            if selection == '1':
                return 'Maori students'
            elif selection == '2':
                return 'Pacific Island students'
            elif selection == '3':
                return 'Specific ethnicity students'
            elif selection == '4':
                return 'Filter on multiple ethnicities'
            elif selection == '5':
                return None  
        else:
            print('\nThat is not a valid option. Please select from the '
                  'available options.')


def get_e_length(status, start, expiry, graduation):
    """Return number of days student has been enrolled.
    
    Calculation is based on student's status. Active and Suspended are
    calculated from start and today dates. Graduated from start and graduation.
    Withdrawn and Cancelled are returned as NaN. Expired from start and expiry.
    Converts dates into a timestamp and then subtracts from today's date (or 
    appropriate date).
    
    Args:
        status (str): Student status.
        start (str): Start date in format DD/MM/YYYY.
        expiry (str): Expiry date in format DD/MM/YYYY.
        graduation (str): Graduation date in format DD/MM/YYYY.
        
    Returns:
        e_length (int): Number of days enrolled.
    """
    if status in ('Active', 'Suspended'):
        # Get today's date
        today = da.get_todays_date()
        # Convert start to a datetime object
        start_date = da.convert_to_datetime(start, '%d/%m/%Y')
        # Subtract today's date from start date
        e_length = da.calculate_days_dt(start_date, today)
    elif status in ('Withdrawn', 'Cancelled'):
        return np.nan
    elif status == 'Graduated':
        # Convert start to a datetime object
        start_date = da.convert_to_datetime(start, '%d/%m/%Y')
        # Convert graduation to a datetime object
        grad_date = da.convert_to_datetime(graduation, '%d/%m/%Y')
        # Subtract graduation date from start date
        e_length = da.calculate_days_dt(start_date, grad_date)
    elif status == 'Expired':
        # Convert start to a datetime object
        start_date = da.convert_to_datetime(start, '%d/%m/%Y')
        # Convert expiry to a datetime object
        expiry_date = da.convert_to_datetime(expiry, '%d/%m/%Y')
        # Subtract expiry date from start date
        e_length = da.calculate_days_dt(start_date, expiry_date)
    else:
        # Empty status or any that is not covered above
        return np.nan
    return e_length


def get_filter_group_option():
    """Get user selection for filter group."""
    selection = False
    while not selection:
        selection = input('\nEnter the number for the filter group you desire.'
                          ' To quit the program, enter quit: ')
        if selection == '1':
            return 'Age'
        elif selection == '2':
            return 'Course'
        elif selection == '3':
            return 'Enrolment Length'
        elif selection == '4':
            return 'Ethnicity'
        elif selection == '5':
            return 'Gender'
        elif selection == '6':
            return 'Status'
        elif selection == '7':
            return 'Tutor'
        elif selection == '8':
            return 'None'
        elif selection.lower() == 'quit':
            print('\nThe app will now quit. No analysis has been performed.')
            sys.exit()
        else:
            print('\n{} is not a valid selection. Please make a valid '
                  'selection.'.format(selection))
            selection = False
            display_avail_filter_groups()        


def get_filter_option(filter_group):
    """Return filter option selected by user.
    
    Args:
        filter_group (str): Filter grouo to select from.
    
    Returns:
        filter_option (str): Filter to be applied.
    """
    filter_option = ''
    if filter_group == 'Age':
        filter_option = get_age_filter()
    elif filter_group == 'Course':
        filter_option = get_course_filter()
    elif filter_group == 'Enrolment Length':
        filter_option = get_enrolment_length_filter()
    elif filter_group == 'Ethnicity':
        filter_option = get_ethnicity_filter()
    elif filter_group == 'Gender':
        filter_option = get_gender_filter()
    elif filter_group == 'Status':
        filter_option = get_status_filter()
    elif filter_group == 'Tutor':
        filter_option = get_tutor_filter()
    else:
        return None
    return filter_option


def get_gender_filter():
    """Return gender filter selection.
    
    Returns:
        selection (str): Gender filter selection.
    """
    # List of allowed selections
    allowed = ['1', '2', '3']
    while True:
        # Display gender filter options
        filter_options_gender_message()
        selection = input('\nPlease enter your selection (number) for the '
                          'gender filter you would like to apply. Enter {} '
                          'if you do not wish to add another filter: '.format(
                                  len(allowed)))
        if selection in allowed:
            if selection == '1':
                return 'Female students'
            elif selection == '2':
                return 'Male students'
            elif selection == '3':
                return None  
        else:
            print('\nThat is not a valid option. Please select from the '
                  'available options.')


def get_module_headings(start_headings, modules, target_module):
    """Return module headings.
    
    Finds the module in the list of modules and then returns each assessment
    name for that module.
    
    Args:
        start_headings (list): Columns to include at start of headings.
        modules (list): List of modules and their assessments (list of lists)
        target_module (str): Module to be processed.
        
    Returns:
        module_headings (list): Module assessment names.
    """
    # Get length of start_headings for removing module name
    name_pos = len(start_headings)
    # Set up initial columns
    module_headings = []
    for column in start_headings:
        module_headings.append(column)
    for module in modules:
        # Find the target_module in the list of modules
        if module[0] == target_module:
            for item in module: # Get headings from module
                module_headings.append(item)
            # Remove module name
            del module_headings[name_pos]
            return module_headings


def get_module_name(module_names):
    """Gets a module name from the user.
    
    Args:
        module_names (list): List of module names.
    
    Returns:
        module_name (str): Name of module.
    """
    # Get selection and make sure it is a valid course
    while True:
        module = input('\nWhat is the name of the module you would like to '
                     'process? For a list of allowed modules, type l. '
                     'Alternatively, type q to quit: ')
        if module == 'q':
            print('\nProgram cancelled. Goodbye.')
            sys.exit()
        elif module == 'l':
            print('\nThe allowed modules are as follows:\n')
            print(module_names)
        elif module in module_names:
            return module
        else:
            print('\nThat is not a valid module. The module must be present in '
                  'the list of valid modules for the course.')


def get_num_assessments(master_headings, non=4):
    """Return the number of assessments.
    
    Returns the length of the master_headings file, less the number of
    non-assessment columns.
    
    Args:
        master_headings (list): Column headings for the master assessment file.
        non (int): Number of columns that are not assessments.
        
    Returns:
        num_assessments (int): Number of assessments.
    """
    return len(master_headings) - non


def get_pacific(ethnicity, islands):
    """Return Pacific Island status.
    
    Checks if the student's ethnicity is a Pacific Island nation. If so,
    returns Yes. If not, returns No.
    
    Args:
        ethnicity (str): Student's ethnicity.
        islands (list): List of Pacific Island nations.
    
    Retrurns:
        ethnicity (str) Yes if ethnicity is found in the Pacific
        Island nations list or No if it is not.
    """
    if ethnicity in islands:
        return 'Yes'
    else:
        return 'No' 


def get_passing_scores(scores, assessments):
    """Return dictionary holding the minimum passing value for each assessment.
    
    Requires that each assessment and its corresponding score are located in
    the same position in each list.
    
    Args:
        scores (list): Minimum passing scores.
        assessments (list): Names of each assessment.
        
    Returns:
        passing_Scores (dict): Passing scores for each assessment.
    """
    passing_scores = {}
    item_pos = 0
    for item in assessments:
        # Assign score value from scores
        passing_scores[assessments[item_pos]] = scores[item_pos]
        # Update position of item
        item_pos += 1
    return passing_scores
    

def get_score_name(course_code):
    """Return file name for assessment scores file.
    
    Extracts the start of the course code and uses this to generate the scores
    file name.
    
    Args:
        course_code (str): Course code in format XXX-XX-XXX. Alternatively,
        just the first part of the course code can be passed for processing.
    
    Returns:
        file_name (str): File name for course.
    """
    # Deal with full course codes
    if len(course_code) > 3:
        # Get location of first hyphen
        hyphen_loc = course_code.index('-')
        # Get first part of the course code
        course = course_code[:hyphen_loc]
    # Deal with just the first part of the code being passed
    else:
        course = course_code
    file_name = 'Scores_{}'.format(course)
    return file_name


def get_status_filter():
    """Return status filter selection.
    
    Returns:
        selection (str): Status filter selection.
    """
    # List of allowed selections
    allowed = ['1', '2', '3', '4', '5', '6', '7', '8']
    while True:
        # Display status filter options
        filter_options_status_message()
        selection = input('\nPlease enter your selection (number) for the '
                          'status filter you would like to apply. Enter {} if '
                          'you do not wish to add another filter: '.format(
                                  len(allowed)))
        if selection in allowed:
            if selection == '1':
                return 'Active'
            elif selection == '2':
                return 'Non-active'
            elif selection == '3':
                return 'Expired'
            elif selection == '4':
                return 'Graduated'
            elif selection == '5':
                return 'Suspended'
            elif selection == '6':
                return 'Withdrawn'
            elif selection == '7':
                return 'Multiple'
            elif selection == '8':
                return None  
        else:
            print('\nThat is not a valid option. Please select from the '
                  'available options.')


def get_tutor_filter():
    """Return tutor filter selection.
    
    Returns:
        selection (str): Course filter selection.
    """
    # List of allowed selections
    allowed = ['1', '2', '3']
    while True:
        # Display tutor filter options
        filter_options_tutor_message()
        selection = input('\nPlease enter your selection (number) for the '
                          'tutor filter you would like to apply. Enter {} if '
                          'you do not wish to add another filter: '.format(
                                  len(allowed)))
        if selection in allowed:
            if selection == '1':
                return 'Specific tutor'
            elif selection == '2':
                return 'Filter on multiple tutors'
            elif selection == '3':
                return None  
        else:
            print('\nThat is not a valid option. Please select from the '
                  'available options.')


def get_value(value_type='', allowed_range=[]):
    """Return user selection for a value.
    
    Gets input from user for a value. Makes sure that the
    input is a valid int and in the allowed_range if supplied.
    
    Args:
        value_type (str): Used for displaying the type of value to the user.
        Can be left blank.
        allowed_range (list): List with two values. First value is lower limit,
        second value is upper limit. Can be left empty if no range checking is
        required.
    
    Returns:
        value (int): User provided value.
    """
    # Modify space for printing to screen correctly
    if value_type not in (None, ''):
        value_type = '{} '.format(value_type)
    # Check allowed_range is valid
    if allowed_range:
        lower = allowed_range[0]
        upper = allowed_range[1]
        # Check lower <= upper
        if lower > upper:
            print('\nLower value ({}) is higher than upper ({}). Allowed range'
                  ' will not be used for calculation. If you need to use the '
                  'range, please correct it and try again.'.format(lower,
                                                                   upper))
            # Remove allowed range so not used
            allowed_range = []
    # No range checking required
    if not allowed_range:
        # Get value and validate
        valid_value = False
        while not valid_value:
            value = input('\nWhat is the {}value? '.format(value_type))
            # Check is a valid int
            if ad.check_is_int(value):
                return int(value)
            else:
                print('\nThat is not a valid number! Please enter a whole '
                      'number.')
    # Check value is within allowed range
    while True:
        # Get value and validate
        valid_value = False
        while not valid_value:
            value = input('\nWhat is the {}value? '.format(value_type))
            # Check is a valid int
            if ad.check_is_int(value):
                # Check is within allowed range
                if value >= lower and value <= upper:
                    return int(value)
                # Value not within allowed range
                else:
                    print('\n{} is not within the allowed range ({} - {}). '
                          'Please select a number between {} and {} inclusive.'
                          .format(value, lower, upper, lower, upper))        
            else:
                print('\nThat is not a valid number! Please enter a whole '
                      'number.')


def get_value_range(value_type=''):
    """Return user selection for lower and upper values.
    
    Gets input from user for lower and upper values. Makes sure that the
    input is a valid int and that lower is <= upper.
    
    Args:
        value_type (str): Used for displaying the type of value to the user.
        Can be left blank.
    
    Returns:
        lower (int): Lower value.
        upper (int): Upper value.
    """
    # Modify space for printing to screen correctly
    if value_type not in (None, ''):
        value_type = '{} '.format(value_type)
    while True:
        # Get lower value and validate
        lower_value = False
        while not lower_value:
            lower = input('\nWhat is the lower {}value? '.format(value_type))
            # Check is a valid int
            if ad.check_is_int(lower):
                lower_value = True
            else:
                print('\nThat is not a valid number! Please enter a whole '
                      'number.')
        # Get upper value
        upper_value = False
        while not upper_value:
            upper = input('What is the upper {}value? '.format(value_type))
            # Check is a valid int
            if ad.check_is_int(upper):
                upper_value = True
            else:
                print('\nThat is not a valid number! Please enter a whole '
                      'number.')
        lower = int(lower)
        upper = int(upper)
        # Check lower <= upper
        if lower <= upper:
            return lower, upper
        else:
            print('\nLower ({}) must be lower or equal to upper ({}). Please '
                  'enter the correct lower and upper values.'.format(lower,
                                                                     upper))


def get_zero_students(student_data, student_ids):
    """Return students with zero completion.
    
    Checks if each student in student_data is in the list of student_ids. If
    not, it checks if there is any text in the last three columns of the
    student' data. If not, the student is added to the list to be returned
    (the student has completed 0% of the course and has not yet been
    processed.)
    
    Args:
        student_data (list): List of lists, one student per list.
        student_ids (list): List of student ids from the analysis data.
        
    Returns:
        students (list) List of returned students. Returns columns 0, 1, 2, 3,
        4 from student_data.
    """
    students = []
    num_students = len(student_data) # For calculating % complete
    n = 0
    for student in student_data:
        # Display progress
        n += 1
        progress = round((n/num_students) * 100)
        print("\rProgress: {}{}".format(progress, '%'), end="", flush=True)
        # Check if student id is in analysis data - process if not
        if student[0] not in student_ids:
            add = True
            # Check if student has been processed previously
            if student[6] not in (None, ''):
                # Don't add student
                add = False
            elif student[7] not in (None, ''):
                # Don't add student
                add = False
            elif student[8] not in (None, ''):
                # Don't add student
                add = False
            # Add student if necessary
            if add:
                # Extract first 5 columns of student's data
                this_student = []
                column = 0
                while column < 5:
                    this_student.append(student[column])
                    column += 1
                students.append(this_student)
    return students


def keep_filters():
    """Return user input for keeping filters.
    
    Returns:
        True if keep and apply filters.
        False if not apply filters (keep original data).
    """
    while True:
        print('\nDo you wish to apply these filters? If so, the data will be '
              'filtered according to these filters. If not, no filtering will '
              'take place and the original data will be analysed.')
        keep = input('\nEnter y to use the filters and n to revert to the '
                     'original data: ')
        if keep.lower() == 'y':
            return True
        elif keep.lower() == 'n':
            return False
        else:
            print('\nThat is not a valid response! Please enter either y or '
                  'n.')

def main():
    repeat = True
    low = 1
    high = 13
    while repeat:
        try_again = False
        main_message()
        try:
            action = int(input('\nPlease enter the number for your '
                               'selection --> '))
        except ValueError:
            print('Please enter a number between {} and {}.'.format(low, high))
            try_again = True
        else:
            if int(action) < low or int(action) > high:
                print('\nPlease select from the available options ({} - {})'
                      .format(low, high))
                try_again = True
            elif action == low:
                create_master_file('Completion')
            elif action == 2:
                create_master_file('Results')
            elif action == 3:
                update_comp_file()
            elif action == 4:
                update_res_file()
            elif action == 5:
                analysis()
            elif action == 6:
                analyse_module()
            elif action == 7:
                check_assesment(True)
            elif action == 8:
                check_assesment(False)
            elif action == 9:
                extract_zero_comp()
            elif action == 10:
                continue
            elif action == 11:
                continue
            elif action == 12:
                continue
            elif action == high:
                print('\nIf you have generated any files, please find them '
                      'saved to disk. Goodbye.')
                sys.exit()
        if not try_again:
            repeat = ad.check_repeat()
    print('\nPlease find your files saved to disk. Goodbye.')


def main_message():
    """Print the menu of options."""
    print('\n\n*************==========================*****************')
    print('\nAssessment Analyser version 0.53')
    print('Created by Jeff Mitchell, 2018')
    print('\nOptions:')
    print('\n1 Create Master Completion File')
    print('2 Create Master Results File')
    print('3 Update Master Completion File')
    print('4 Update Master Results File')
    print('5 Perform Analysis')
    print('6 Analyse Module')
    print('7 Assessment Completed Report')
    print('8 Assessment Not Completed Report')
    print('9 Identify Expired Students 0% Completion')
    print('10 Identify Expired Students At Least X% Completion')
    print('11 Identify Expired Students Between X% and Y% Completion')
    print('12 Identify Graduated Students')
    print('13 Exit')


def process_age_filter(lower, upper, comp_data, res_data):
    """Apply age filter to data.
    
    Applies the selected age filter to the Completion and Results data. Only
    rows meeting the filter condition are returned. If the filter will result
    in no rows being returned, the filter is discarded and the passed data is
    returned.
    
    Args:
        lower (int): Lowest value for age range.
        upper (int): Highest value for age range.
        comp_data (dataframe): Completion data.
        res_data (dataframe): Results data.
    
    Returns:
        filtered_comp_data (dataframe): Filtered Completion data.
        filtered_res_data (dataframe): Filtered Results data.
        valid_filter (bool): True if filter has been applied, False if not.
    """
    # Make copy of dataframes in case need to revert
    filtered_comp_data = comp_data.copy()
    filtered_res_data = res_data.copy()
    # Convert ages outside lower and upper values to NaN
    filtered_comp_data['Age'] = filtered_comp_data['Age'].apply(
            apply_age_filter, args=(lower, upper,))
    filtered_res_data['Age'] = filtered_res_data['Age'].apply(
            apply_age_filter, args=(lower, upper,))
    # Drop ages that are NaN
    filtered_comp_data.dropna(subset=['Age'], inplace=True)
    filtered_res_data.dropna(subset=['Age'], inplace=True)
    # Check that filter returns at least one row
    if filtered_comp_data.empty or filtered_comp_data.empty:
        # Return original data
        valid_filter = False
        return comp_data, res_data, valid_filter
    else:
        # Return updated data
        valid_filter = True
        return filtered_comp_data, filtered_res_data, valid_filter
        

def process_course_filter(filter_option, comp_data, res_data):
    """Apply course filter to data.
    
    Applies the selected course filter to the Completion and Results data. Only
    rows meeting the filter condition are returned. If the filter will result
    in no rows being returned, the filter is discarded and the passed data is
    returned.
    
    Args:
        filter_option (str): Filter option to be applied.
        comp_data (dataframe): Completion data.
        res_data (dataframe): Results data.
    
    Returns:
        filtered_comp_data (dataframe): Filtered Completion data.
        filtered_res_data (dataframe): Filtered Results data.
        valid_filter (bool): True if filter has been applied, False if not.
    """
    # Make copy of dataframes in case need to revert
    filtered_comp_data = comp_data.copy()
    filtered_res_data = res_data.copy()
    # Apply passed filter
    if filter_option == 'Online students':
        # Convert non-online courses to NaN
        filtered_comp_data['Course'] = filtered_comp_data['Course'].apply(
                apply_course_filter, args=('ON',))
        filtered_res_data['Course'] = filtered_res_data['Course'].apply(
                apply_course_filter, args=('ON',))
        # Drop courses that are NaN
        filtered_comp_data.dropna(subset=['Course'], inplace=True)
        filtered_res_data.dropna(subset=['Course'], inplace=True)
    elif filter_option == 'Part-time students':
        # Convert non-part-time courses to NaN
        filtered_comp_data['Course'] = filtered_comp_data['Course'].apply(
                apply_course_filter, args=('PT',))
        filtered_res_data['Course'] = filtered_res_data['Course'].apply(
                apply_course_filter, args=('PT',))
        # Drop courses that are NaN
        filtered_comp_data.dropna(subset=['Course'], inplace=True)
        filtered_res_data.dropna(subset=['Course'], inplace=True)
    elif filter_option == 'CPD students':
        # Convert non-cpd courses to NaN
        filtered_comp_data['Course'] = filtered_comp_data['Course'].apply(
                apply_course_filter, args=('CPD',))
        filtered_res_data['Course'] = filtered_res_data['Course'].apply(
                apply_course_filter, args=('CPD',))
        # Drop courses that are NaN
        filtered_comp_data.dropna(subset=['Course'], inplace=True)
        filtered_res_data.dropna(subset=['Course'], inplace=True)
    elif filter_option == 'Specific course students':
        # Load list of valid course codes
        # Get specific course
        course = 'ADV-PT-006' # Temp working value
        # Check if course exists
        # Filter based on course
        filtered_comp_data['Course'] = filtered_comp_data['Course'].apply(
                apply_course_filter, args=(course,False))
        filtered_res_data['Course'] = filtered_res_data['Course'].apply(
                apply_course_filter, args=(course,False))
        # Drop courses that are NaN
        filtered_comp_data.dropna(subset=['Course'], inplace=True)
        filtered_res_data.dropna(subset=['Course'], inplace=True)
    # Check that filter returns at least one row
    if filtered_comp_data.empty or filtered_comp_data.empty:
        # Return original data
        valid_filter = False
        return comp_data, res_data, valid_filter
    else:
        # Return updated data
        valid_filter = True
        return filtered_comp_data, filtered_res_data, valid_filter 


def process_el_filter(filter_option, comp_data, res_data):
    """Apply enrolment length filter to data.
    
    Applies the selected enrolment length filter to the Completion and Results
    data. Only rows meeting the filter condition are returned. If the filter
    will result in no rows being returned, the filter is discarded and the 
    passed data is returned.
    
    Args:
        filter_option (str): Filter option to be applied.
        comp_data (dataframe): Completion data.
        res_data (dataframe): Results data.
    
    Returns:
        filtered_comp_data (dataframe): Filtered Completion data.
        filtered_res_data (dataframe): Filtered Results data.
        valid_filter (bool): True if filter has been applied, False if not.
    """
    # Make copy of dataframes in case need to revert
    filtered_comp_data = comp_data.copy()
    filtered_res_data = res_data.copy()
    # Apply passed filter
    if filter_option == 'No more than x days enrolled':
        # Get max days enrolled
        maximum = get_value('maximum days enrolled')
        # Convert enrolment lenghts outside filter to NaN
        filtered_comp_data['EnrolLength'] = filtered_comp_data[
                'EnrolLength'].apply(apply_el_filter_below, args=(maximum,))
        filtered_res_data['EnrolLength'] = filtered_comp_data[
                'EnrolLength'].apply(apply_el_filter_below, args=(maximum,))
        # Drop enrolment lengths that are NaN
        filtered_comp_data.dropna(subset=['EnrolLength'], inplace=True)
        filtered_res_data.dropna(subset=['EnrolLength'], inplace=True)
    elif filter_option == 'No less than x days enrolled':
        # Get min days enrolled
        minimum = get_value('minimum days enrolled')
        # Convert enrolment lenghts outside filter to NaN
        filtered_comp_data['EnrolLength'] = filtered_comp_data[
                'EnrolLength'].apply(apply_el_filter_above, args=(minimum,))
        filtered_res_data['EnrolLength'] = filtered_comp_data[
                'EnrolLength'].apply(apply_el_filter_above, args=(minimum,))
        # Drop enrolment lengths that are NaN
        filtered_comp_data.dropna(subset=['EnrolLength'], inplace=True)
        filtered_res_data.dropna(subset=['EnrolLength'], inplace=True)
    elif filter_option == 'Between x and y days enrolled':
        # Get min days enrolled
        minimum, maximum = get_value_range('days enrolled')
        # Convert enrolment lenghts outside filter to NaN
        filtered_comp_data['EnrolLength'] = filtered_comp_data[
                'EnrolLength'].apply(apply_el_filter_between, args=(minimum,
                maximum,))
        filtered_res_data['EnrolLength'] = filtered_comp_data[
                'EnrolLength'].apply(apply_el_filter_between, args=(minimum,
                maximum,))
        # Drop enrolment lengths that are NaN
        filtered_comp_data.dropna(subset=['EnrolLength'], inplace=True)
        filtered_res_data.dropna(subset=['EnrolLength'], inplace=True)
    # Check that filter returns at least one row
    if filtered_comp_data.empty or filtered_comp_data.empty:
        # Return original data
        valid_filter = False
        return comp_data, res_data, valid_filter
    else:
        # Return updated data
        valid_filter = True
        return filtered_comp_data, filtered_res_data, valid_filter 


def process_ethnicity_filter(filter_option, comp_data, res_data):
    """Apply ethnicity filter to data.
    
    Applies the selected ethnicity filter to the Completion and Results data.
    Only rows meeting the filter condition are returned. If the filter will
    result in no rows being returned, the filter is discarded and the passed
    data is returned.
    
    Args:
        filter_option (str): Filter option to be applied.
        comp_data (dataframe): Completion data.
        res_data (dataframe): Results data.
    
    Returns:
        filtered_comp_data (dataframe): Filtered Completion data.
        filtered_res_data (dataframe): Filtered Results data.
        valid_filter (bool): True if filter has been applied, False if not.
    """
    # Make copy of dataframes in case need to revert
    filtered_comp_data = comp_data.copy()
    filtered_res_data = res_data.copy()
    # Apply passed filter
    if filter_option == 'Maori students':
        # Convert non-maori students to NaN
        filtered_comp_data['Ethnicity'] = filtered_comp_data[
                'Ethnicity'].apply(apply_filter, args=('Maori',))
        filtered_comp_data['Ethnicity'] = filtered_comp_data[
                'Ethnicity'].apply(apply_filter, args=('Maori',))
        # Drop courses that are NaN
        filtered_comp_data.dropna(subset=['Ethnicity'], inplace=True)
        filtered_res_data.dropna(subset=['Ethnicity'], inplace=True)
    elif filter_option == 'Pacific Island students':
        # Convert non-pacific students to NaN
        filtered_comp_data['Pacific'] = filtered_comp_data['Pacific'].apply(
                apply_pacific_filter, args=(True,))
        filtered_res_data['Pacific'] = filtered_res_data['Pacific'].apply(
                apply_pacific_filter, args=(True,))
        # Drop courses that are NaN
        filtered_comp_data.dropna(subset=['Pacific'], inplace=True)
        filtered_res_data.dropna(subset=['Pacific'], inplace=True)
    elif filter_option == 'Specific ethnicity students':
        # Get ethnicity
        target_ethnicity = 'NZ European' # Temp value
        # Convert non-target etnicity students to NaN
        filtered_comp_data['Ethnicity'] = filtered_comp_data[
                'Ethnicity'].apply(apply_filter, args=(target_ethnicity,))
        filtered_comp_data['Ethnicity'] = filtered_comp_data[
                'Ethnicity'].apply(apply_filter, args=(target_ethnicity,))
        # Drop students that are NaN
        filtered_comp_data.dropna(subset=['Ethnicity'], inplace=True)
        filtered_res_data.dropna(subset=['Ethnicity'], inplace=True)
    elif filter_option == 'Filter on multiple ethnicities':
        # To complete
        print('\nFunction to be written.')
    # Check that filter returns at least one row
    if filtered_comp_data.empty or filtered_comp_data.empty:
        # Return original data
        valid_filter = False
        return comp_data, res_data, valid_filter
    else:
        # Return updated data
        valid_filter = True
        return filtered_comp_data, filtered_res_data, valid_filter


def process_gender_filter(filter_option, comp_data, res_data):
    """Apply gender filter to data.
    
    Applies the selected gender filter to the Completion and Results data.
    Only rows meeting the filter condition are returned. If the filter will
    result in no rows being returned, the filter is discarded and the passed
    data is returned.
    
    Args:
        filter_option (str): Filter option to be applied.
        comp_data (dataframe): Completion data.
        res_data (dataframe): Results data.
    
    Returns:
        filtered_comp_data (dataframe): Filtered Completion data.
        filtered_res_data (dataframe): Filtered Results data.
        valid_filter (bool): True if filter has been applied, False if not.
    """
    # Make copy of dataframes in case need to revert
    filtered_comp_data = comp_data.copy()
    filtered_res_data = res_data.copy()
    # Apply passed filter
    if filter_option == 'Female students':
        # Convert non-female students to NaN
        filtered_comp_data['Gender'] = filtered_comp_data[
                'Gender'].apply(apply_filter, args=('Female',))
        filtered_res_data['Gender'] = filtered_res_data[
                'Gender'].apply(apply_filter, args=('Female',))
        # Drop courses that are NaN
        filtered_comp_data.dropna(subset=['Gender'], inplace=True)
        filtered_res_data.dropna(subset=['Gender'], inplace=True)
    elif filter_option == 'Male students':
        # Convert non-male students to NaN
        filtered_comp_data['Gender'] = filtered_comp_data[
                'Gender'].apply(apply_filter, args=('Male',))
        filtered_res_data['Gender'] = filtered_res_data[
                'Gender'].apply(apply_filter, args=('Male',))
        # Drop students that are NaN
        filtered_comp_data.dropna(subset=['Gender'], inplace=True)
        filtered_res_data.dropna(subset=['Gender'], inplace=True)
    # Check that filter returns at least one row
    if filtered_comp_data.empty or filtered_comp_data.empty:
        # Return original data
        valid_filter = False
        return comp_data, res_data, valid_filter
    else:
        # Return updated data
        valid_filter = True
        return filtered_comp_data, filtered_res_data, valid_filter


def process_status_filter(filter_option, comp_data, res_data):
    """Apply status filter to data.
    
    Applies the selected status filter to the Completion and Results data.
    Only rows meeting the filter condition are returned. If the filter will
    result in no rows being returned, the filter is discarded and the passed
    data is returned.
    
    Args:
        filter_option (str): Filter option to be applied.
        comp_data (dataframe): Completion data.
        res_data (dataframe): Results data.
    
    Returns:
        filtered_comp_data (dataframe): Filtered Completion data.
        filtered_res_data (dataframe): Filtered Results data.
        valid_filter (bool): True if filter has been applied, False if not.
    """
    # Make copy of dataframes in case need to revert
    filtered_comp_data = comp_data.copy()
    filtered_res_data = res_data.copy()
    # Apply passed filter TO DO
    if filter_option == 'Multiple':
        # To complete
        print('\nFunction to be written.')
    elif filter_option == 'Non-active':
        # Convert active students to NaN
        filtered_comp_data['Status'] = filtered_comp_data['Status'].apply(
                apply_filter, args=('Active',False,))
        filtered_res_data['Status'] = filtered_res_data['Status'].apply(
                apply_filter, args=('Active',False,))
        # Drop students that are NaN
        filtered_comp_data.dropna(subset=['Status'], inplace=True)
        filtered_res_data.dropna(subset=['Status'], inplace=True)
    elif filter_option:
        # Convert non-matching students to NaN
        filtered_comp_data['Status'] = filtered_comp_data['Status'].apply(
                apply_filter, args=(filter_option,))
        filtered_res_data['Status'] = filtered_res_data['Status'].apply(
                apply_filter, args=(filter_option,))
        # Drop students that are NaN
        filtered_comp_data.dropna(subset=['Status'], inplace=True)
        filtered_res_data.dropna(subset=['Status'], inplace=True)
    # Check that filter returns at least one row
    if filtered_comp_data.empty or filtered_comp_data.empty:
        # Return original data
        valid_filter = False
        return comp_data, res_data, valid_filter
    else:
        # Return updated data
        valid_filter = True
        return filtered_comp_data, filtered_res_data, valid_filter


def process_tutor_filter(filter_option, comp_data, res_data):
    """Apply tutor filter to data.
    
    Applies the selected status filter to the Completion and Results data.
    Only rows meeting the filter condition are returned. If the filter will
    result in no rows being returned, the filter is discarded and the passed
    data is returned.
    
    Args:
        filter_option (str): Filter option to be applied.
        comp_data (dataframe): Completion data.
        res_data (dataframe): Results data.
    
    Returns:
        filtered_comp_data (dataframe): Filtered Completion data.
        filtered_res_data (dataframe): Filtered Results data.
        valid_filter (bool): True if filter has been applied, False if not.
    """
    # Make copy of dataframes in case need to revert
    filtered_comp_data = comp_data.copy()
    filtered_res_data = res_data.copy()
    # Apply passed filter TO DO
    if filter_option == 'Specific tutor':
        # To complete
        print('\nFunction to be written.')
    elif filter_option == 'Filter on multiple tutors':
        # To complete
        print('\nFunction to be written.')
    # Check that filter returns at least one row
    if filtered_comp_data.empty or filtered_comp_data.empty:
        # Return original data
        valid_filter = False
        return comp_data, res_data, valid_filter
    else:
        # Return updated data
        valid_filter = True
        return filtered_comp_data, filtered_res_data, valid_filter


def process_unknown_names(names, course):
    """Display unknown names and save to file.
    
    If there are unknown names, they are displayed and saved to a text file.
    User is given the option to continue (in which case they will need to 
    update the Master File manually for the unknown students) or to quit so 
    that they can update the Enrolment IDs file wit the correct names before
    processing again.
    
    Args:
        names (set): Names that are not recognised.
        course (str): Course code for save file name.
    """
    if names:
        print('\nCould not find the Student ID for the following students. '
              'They need to be processed manually.')
        print('Note that if they have been transferred to another course, they'
              ' can be ignored as they will be picked up in the new course.\n')
        print(names)
        f_name = 'Unknown_students_{}_{}.txt'.format(course,
                                   ft.generate_time_string())
        ft.save_list_to_text(names, f_name)
        print('\nIf you continue, you will need to update the Master File '
              'manually to add these students. Alterntaively, you can quit the'
              ' program now and add these students to the Enrolment_IDs file '
              'before processing again.')
        while True:
            action = input('\nDo you wish to continue? Enter y to continue or '
                           'n to quit: ')
            if action == 'n':
                print('\nProgram cancelled. Goodbye.')
                sys.exit()
            elif action == 'y':
                return
            else:
                print('\nThat is not a valid response.')
    else:
        print('\nNo unknown names found.')
            

def remove_duplicated(assessments, duplicates, course):
    """Saves data for duplicated names and removes that data from enrolments.
    
    Students that share the same name will not be able to have their Enrolment
    ID and Student ID added to the data. To prevent this, students with
    duplicate names are extracted from the data to be processed separately.
    Their data is saved, the list of names is printed to the screen, and the
    data for students with the duplicated names is removed from the enrolment
    dataset.
    
    Args:
        assessments (list): List of lists with assessment data.
        duplicates (list): List of duplicated student names.
        course (str): Course code. Used for save file name.
        
    Returns:
        updated_assessments (list): Student assessments with duplicated student
        names' entries removed.
    """
    duplicate_assessments = [] # To hold entries for found duplicates
    duplicate_names = set() # To hold names that have been extracted
    updated_assessments = [] # To hold non-duplicates
    # Check each record for a duplicate name
    for record in assessments:
        if record[1] in duplicates:
            duplicate_assessments.append(record)
            duplicate_names.add(record[1])
        else:
            updated_assessments.append(record)
    # Print out list of duplicates removed
    if not duplicate_names:
        print('\nNo duplicated names were found.')
    else:
        print('\nStudents that have been removed due to duplicate names:')
        ad.debug_list(list(duplicate_names))
        # Save duplicated data
        file_name = '{}_Duplicate_Name_Assessments_{}.txt'.format(course,
                     ft.generate_time_string())
        ft.save_list_to_text(duplicate_assessments, file_name)
        print('\nDuplicated students saved to {}. Please process these students '
              'manually.'.format(file_name))
    # Return updated_assessments
    return updated_assessments


def update_comp_file():
    """Update Master Completion File."""
    warnings = ['\nProcessing Master Completion Update Data Warnings:\n']
    warnings_to_process = False
    print('\nProcessing Assessment Data.')
    # Confirm the required files are in place
    required_files = ['Course Codes File', 'Assessment Data File',
                      'Enrolment IDs File', 'Duplicate Names File',
                      'Master Completion File',
                      'Master Completion Headings File',
                      'Assessment Data Headings File', 'Assessment Scores',
                      'Assessment Names File']
    ad.confirm_files('Process Master Completion Update Data', required_files)
    # Get course code to process
    course_code = get_course_code()
    # Load assessment data file
    print('\nLoading {}...'.format('{} Assessment Data File'.format(
            course_code)))
    assessment_data = ft.get_csv_fname_load('{} Assessment Data File'.format(
            course_code))
    print('Loaded {}.'.format('{} Assessment Data File'.format(course_code)))
    # Load Enrolment data (e_id, s_id, Name, Course) into a list of lists
    print('\nLoading {}...'.format('Enrolment_IDs_{}.csv'.format(course_code)))
    enrolments = ft.load_csv('Enrolment_IDs_{}.csv'.format(course_code))
    print('Loaded {}.'.format('Enrolment_IDs_{}.csv'.format(course_code)))
    # Load list of duplicate names
    print('\nLoading {}...'.format('Duplicate_Names_{}'.format(course_code)))
    duplicates = ft.load_headings('Duplicate_Names_{}'.format(course_code),
                                  'e')
    print('Loaded {}.'.format('Duplicate_Names_{}'.format(course_code)))
    # Extract data for students on duplicates list and remove from assessments
    assessment_data = remove_duplicated(assessment_data, duplicates,
                                        course_code)
    # Add student and enrolment IDs and Course to assessment data
    assessment_data, unknown_names = db.add_ids(enrolments, assessment_data, 1)
    # Process unknown names so can be added manually or fixed and repeated
    process_unknown_names(unknown_names, course_code)
    # Place assessment_data into a DataFrame
    # Load Assessments headings file
    print('\nLoading {}...'.format('Assessment_Data_Headings.txt'))
    assessment_headings = ft.load_headings('Assessment_Data_Headings', 'e')
    print('Loaded {}.'.format('Assessment_Data_Headings.txt'))
    assessments_df = pd.DataFrame(data = assessment_data,
                                  columns = assessment_headings)
    # Load assessment names file
    print('\nLoading {}...'.format('Assessment_Names_{}'.format(course_code)))
    assessments = ft.load_headings('Assessment_Names_{}'.format(course_code),
                                       'e')
    print('Loaded {}.'.format('Assessment_Names_{}'.format(course_code)))
    # Check there are entries to process
    check_df(assessments_df)
    # Drop Unknown students so can be done manually
    assessments_df['EnrolmentID'] = assessments_df['EnrolmentID'].apply(
            ad.convert_to_nan, args=(['Unknown'],))
    assessments_df.dropna(subset=['EnrolmentID'], inplace=True)
    # Check there are entries to process
    check_df(assessments_df)
    # Process transferred students for the month first
    transfers_df = assessments_df.copy()
    # Drop rows where feedback column does not have 'transferred' etc
    transfers_df['Feedback text'] = transfers_df['Feedback text'].apply(
            find_transferred)
    transfers_df.dropna(subset=['Feedback text'], inplace=True)
    # Drop columns so left with EnrolmentID, Name, Course, Grade Item
    revised_headings = ['EnrolmentID', 'StudentID','Name', 'Course',
                        'Grade item']
    transfers_df = transfers_df[revised_headings]
    '''
    transfers_df.to_csv('Transfer_df_check_{}.csv'.format(
            ft.generate_time_string()), index=False)
    '''
    # Load master file for course
    print('\nLoading {}...'.format('Master_Completion_{}.csv'.format(
            course_code)))
    master_data = ft.load_csv('Master_Completion_{}.csv'.format(course_code))
    print('Loaded {}.'.format('Master_Completion_{}.csv'.format(course_code)))
    # Load Master headings file
    print('\nLoading {}...'.format('Master_Completion_Headings_{}'.format
          (course_code)))
    master_headings = ft.load_headings('Master_Completion_Headings_{}'.format
                                       (course_code), 'e')
    print('Loaded {}.'.format('Master_Completion_Headings_{}'.format
          (course_code)))
    # Update Master File - add 'Transferred' in appropriate Grade Item column
    transferred_master = update_grades_comp_trans(master_data, transfers_df,
                                                  assessments)
    '''
    ft.save_list_csv(transferred_master, master_headings,
                     'Transfer_Check_{}.csv'.format(ft.generate_time_string()))
    '''
    # Now process assessments completed this month with the original data
    # Drop non-assessment entries
    assessments_df['Grade item'] = assessments_df['Grade item'].apply(
            ad.convert_to_nan, args=(['Course total'],))
    assessments_df.dropna(subset=['Grade item'], inplace=True)
    # Check there are entries to process
    check_df(assessments_df)
    # Load assessment scores
    scores_name = get_score_name(course_code)
    print('\nLoading {}...'.format(scores_name))
    scores = ft.load_headings(scores_name, 'e')
    print('Loaded {}.'.format(scores_name))
    # Convert scores to ints
    scores = convert_scores(scores)
    # Create dictionary to hold passing scores for each assessment
    passing_scores = get_passing_scores(scores, assessments)
    # ad.debug_dict(passing_scores)
    # Convert Revised grades to a float (currently string)
    assessments_df['Revised grade'] = assessments_df['Revised grade'].apply(
            ad.convert_to_float)
    # Convert Revised grades to int (will round down to nearest whole number)
    assessments_df['Revised grade'] = assessments_df['Revised grade'].apply(
            ad.convert_to_int)
    # Drop entries that do not pass
    # Create a column to hold passing status of all entries
    assessments_df['Passing'] = assessments_df.apply(lambda x: check_scores(x
                  ['Revised grade'], x['Grade item'], passing_scores), axis=1)
    assessments_df.dropna(subset=['Passing'], inplace=True)
    # Check there are entries to process
    check_df(assessments_df)
    # Get just desired columns
    revised_headings = ['EnrolmentID', 'StudentID','Date and time', 'Name',
                        'Course', 'Grade item']
    assessments_df = assessments_df[revised_headings]
    # Extract Month and Year from Date and time column
    assessments_df['Date and time'] = assessments_df['Date and time'].apply(
            extract_month_year)
    # Convert Month and Year to Mmm-YY
    assessments_df['Date and time'] = assessments_df['Date and time'].apply(
            da.convert_to_mmm_yy)
    # Temp save to check
    assessments_df.to_csv('assessments_check_{}.csv'.format(
            ft.generate_time_string()), index=False)
    # Update Master file with assessment dates
    updated_master = update_grades_comp(transferred_master, assessments_df,
                                   assessments)
    master_name = 'Master_Completion_{}_'.format(course_code)
    ft.save_list_csv(updated_master, master_headings, master_name)
    ft.process_warning_log(warnings, warnings_to_process)


def update_grades_comp(master, assessments_df, assessment_names):
    """Updates Master Completions file with completed assessments grades.
    
    For each record in assessments, allocates to the grade item the month that
    the assessment was completed, in the row in the master file for the
    enrolment ID.
    
    Args:
        master (list): Master record of all assessments for each student.
        assessments_df (dataframe): Current month assessments to be updated.
        assessment_names (list): List of each assessment name.
    
    Returns:
        updated_master (list): Updated with current month assessments.
    """
    updated_master = copy.deepcopy(master)
    # Get a list of the EnrolmentID's in updated_master
    students = db.get_ids(updated_master, 0)
    # List to hold students that get added to updated_master
    added = [] 
    print('\nUpdating Master File (Completions)')
    num_assessments = assessments_df.shape[0] # For calculating % complete
    n = 1
    # Process each record in assessments
    for index, row in assessments_df.iterrows():
        # Display progress
        progress = round((n/num_assessments) * 100)
        print("\rProgress: {}{}".format(progress, '%'), end="", flush=True)
        # Get column to update
        # (add 4 to skip the non-assessment columns in Master dataframe)
        col_pos = assessment_names.index(row['Grade item']) + 4
        # Check if enrolment ID present in updated_master and process
        if row['EnrolmentID'] in students or row['EnrolmentID'] in added:
            # Find the student in master
            for student in updated_master:
                # print(student)
                if student[0] == row['EnrolmentID']:
                    # Check that entry is empty
                    #print(col_pos)
                    #print(student)
                    if student[col_pos] in (None, ''):
                        # Update assessment with month, year completed
                        student[col_pos] = row['Date and time']
                        break
        # Not present - create entry
        else:
            # Add student to added list so get updated correctly if found again
            added.append(row['EnrolmentID'])
            # Create new student record
            new_student = []
            new_student.append(row['EnrolmentID'])
            new_student.append(row['StudentID'])
            new_student.append(row['Name'])
            new_student.append(row['Course'])
            # Add each assessment, set to ''
            assessments_total = len(assessment_names)
            for i in range(assessments_total):
                new_student.append('')
            # Update present assessment
            new_student[col_pos] = row['Date and time']
            # Add to updated_master
            updated_master.append(new_student)
        n += 1
    print('\rFinished processing Assessment Data\n')
    return updated_master
    

def update_grades_comp_trans(master, assessments_df, assessment_names):
    """Updates Master Completions file with transferred assessments.
    
    For each record in assessments, allocates to the grade item 'Transferred'
    in the row in the master file for the enrolment ID.
    
    Args:
        master (list): Master record of all assessments for each student.
        assessments_df (dataframe): Current month assessments to be transferred.
        assessment_names (list): List of each assessment name.
    
    Returns:
        updated_master (list): Updated with current month assessments.
    """
    '''
    assessments_df.to_csv('transfer_assessments_update_master_{}.csv'.format(
            ft.generate_time_string()), index=False)
    '''
    updated_master = copy.deepcopy(master)
    # Get a list of the EnrolmentID's in updated_master
    students = db.get_ids(updated_master, 0)
    # List to hold students that get added to updated_master
    added = [] 
    print('\nUpdating Master Completion File (Transfers)')
    num_assessments = assessments_df.shape[0] # For calculating % complete
    n = 1
    # Process each record in assessments
    for index, row in assessments_df.iterrows():
        # Display progress
        progress = round((n/num_assessments) * 100)
        print("\rProgress: {}{}".format(progress, '%'), end="", flush=True)
        # Get column to update
        # (add 4 to skip the non-assessment columns in Master dataframe)
        col_pos = assessment_names.index(row['Grade item']) + 4
        # Check if enrolment ID present in updated_master and process
        if row['EnrolmentID'] in students or row['EnrolmentID'] in added:
            # Find the student in master
            for student in updated_master:
                if student[0] == row['EnrolmentID']:
                    student[col_pos] = 'Transferred'
                    break
        # Not present - create entry
        else:
            # Add student to added list so get updated correctly if found again
            added.append(row['EnrolmentID'])
            # Create new student record
            new_student = []
            new_student.append(row['EnrolmentID'])
            new_student.append(row['StudentID'])
            new_student.append(row['Name'])
            new_student.append(row['Course'])
            # Add each assessment, set to ''
            assessments_total = len(assessment_names)
            for i in range(assessments_total):
                new_student.append('')
            # Update present assessment
            new_student[col_pos] = 'Transferred'
            # Add to updated_master
            updated_master.append(new_student)
        n += 1
    print('\rFinished processing Assessment Data')
    # Make sure each student has the correct number of items
    # One per assessment + 4 identifiers
    for item in updated_master:
        num_items = len(assessment_names) + 4
        if len(item) != num_items:
            print('Warning! {} data is {} in length'.format(item[2],len(item)))
        # print(item)
    return updated_master


def update_grades_res(master, assessments_df, assessment_names):
    """Updates Master Results file with completed assessments grades and dates.
    
    For each record in assessments, allocates to the grade item the month that
    the assessment was completed, in the row in the master file for the
    enrolment ID.
    
    Args:
        master (list): Master record of all results for each student.
        assessments_df (dataframe): Current month assessments to be updated.
        assessment_names (list): List of each assessment name and date as per
        Results Master headings.
    
    Returns:
        updated_master (list): Updated with current month results.
    """
    updated_master = copy.deepcopy(master)
    # Get a list of the EnrolmentID's in updated_master
    students = db.get_ids(updated_master, 0)
    # List to hold students that get added to updated_master
    added = [] 
    print('\nUpdating Master File (Results)')
    num_assessments = assessments_df.shape[0] # For calculating % complete
    n = 1
    # Process each record in assessments
    for index, row in assessments_df.iterrows():
        # Display progress
        progress = round((n/num_assessments) * 100)
        print("\rProgress: {}{}".format(progress, '%'), end="", flush=True)
        # Get column to update
        col_pos = assessment_names.index(row['Grade item'])
        # Check if enrolment ID present in updated_master and process
        if row['EnrolmentID'] in students or row['EnrolmentID'] in added:
            # Find the student in master
            for student in updated_master:
                # print(student)
                if student[0] == row['EnrolmentID']:
                    # Check that entry is empty
                    #print(col_pos)
                    #print(student)
                    if student[col_pos] in (None, ''):
                        # Update Grade with 'Competent'
                        student[col_pos] = row['Revised grade']
                        # Update Date with completion date
                        student[col_pos+1] = row['Date and time']
                        # Remove timestamp info
                        # student[col_pos+1] = student[col_pos+1].dt.date
                        break
        # Not present - create entry
        else:
            # Add student to added list so get updated correctly if found again
            added.append(row['EnrolmentID'])
            # Create new student record
            new_student = []
            new_student.append(row['EnrolmentID'])
            new_student.append(row['StudentID'])
            new_student.append(row['Name'])
            new_student.append(row['Course'])
            # Add each assessment, set to ''
            assessments_total = len(assessment_names) - 4 # Remove student info
            for i in range(assessments_total):
                new_student.append('')
            # Update Grade with 'Competent'
            new_student[col_pos] = row['Revised grade']
            # Update Date with completion date
            new_student[col_pos+1] = row['Date and time']
            # Remove timestamp info
            # new_student[col_pos+1]
            # Add to updated_master
            updated_master.append(new_student)
        n += 1
    print('\rFinished processing Assessment Data\n')
    return updated_master


def update_module_completion(student, module, modules_dict, month_order,
                             transfers=True):
    """Return completion status for a module.
    
    For the provided module, determines if the student has completed all of the
    required assesments. If they have, the date the final assessment was
    completed is returned. If they have not, the empty string is returned.
    
    Args:
        student (DataFrame): Row of assessment data for student.
        module (str): Module being checked
        moddules_dict (dict): Modules and required assessments.
        month_order (list): List containing each month in order.
        transfers (bool): Whether to keep transferred assessments in analysis
             - True: students with transferred assessments still have them
             counted towards module completion date. 
             - False: students with at least one transferred assessment
             are listed as 'Transferred' in month column.
    
    Returns:
        status (str): Completion status for the module.    
    """
    status = ''
    months = set() # Hold completion month for each assessment
    for assessment in modules_dict[module]:
        if not student[assessment]:
            # Assessment is False - has not been completed
            return status
        else:
            # Add month completed
            months.add(student[assessment])
    # All completed
    months = list(months)
    if not transfers:
        # Retrun 'Transferred' if any assessments transferred
        if 'Transferred' in months:
            return 'Transferred'
    # Drop Transferred assessments
    if 'Transferred' in months:
        months.remove('Transferred')
    # If no assessments left, return 'Transferred'
    if not months:
        return 'Transferred'
    # If only one month, return that month
    elif len(months) == 1:
        return months[0]
    # - TO DO: Calculate last month and return
    else:
        status = get_completion_month(months, month_order)
    return status


def update_num_ass_col(student, assessments):
    """Return number of assessments completed by a student.
    
    Counts each assessment the student has completed (non-blank) and then
    returns this count. Can also be used for counting completed modules etc.
    
    Args:
        student (DataFrame): Row of assessment data for student.
        assessments (list): Assessment columns.
        
    Returns:
        assess_count (int): Number of completed assessments.
    """
    num_assess = 0
    for assessment in assessments:
        if student[assessment]:
            num_assess += 1
    return num_assess


def update_perc_comp_col(completed, total):
    """Return percentage of assessments completed by a student.
    
    Divides the number of assessments completed by the total number of
    assessments. Rounds the number to two decimal places.
    
    Args:
        completed (int): Number of assessments completed.
        total (int): Number of assessments in course.
        
    Returns:
        assess_perc (float): Percentage of completed assessments.
    """
    return round((completed / total), 2)


def update_res_file():
    """Update Master Results File."""
    warnings = ['\nProcessing Master Results Update Data Warnings:\n']
    warnings_to_process = False
    print('\nProcessing Assessment Data.')
    # Confirm the required files are in place
    required_files = ['Course Codes File', 'Assessment Data File',
                      'Enrolment IDs File', 'Duplicate Names File',
                      'Master Results File',
                      'Master Results Headings File',
                      'Assessment Data Headings File', 'Assessment Scores',
                      'Assessment Names File']
    ad.confirm_files('Process Master Results Update Data', required_files)
    # Get course code to process
    course_code = get_course_code()
    # (C) means can copy and modify from update_comp_file()
    # (N) means a new function will need to be written for this
    # Load assessment data file
    print('\nLoading {}...'.format('{} Assessment Data File'.format(
            course_code)))
    assessment_data = ft.get_csv_fname_load('{} Assessment Data File'.format(
            course_code))
    print('Loaded {}.'.format('{} Assessment Data File'.format(course_code)))
    # Load Enrolment data (e_id, s_id, Name, Course) into a list of lists
    print('\nLoading {}...'.format('Enrolment_IDs_{}.csv'.format(course_code)))
    enrolments = ft.load_csv('Enrolment_IDs_{}.csv'.format(course_code))
    print('Loaded {}.'.format('Enrolment_IDs_{}.csv'.format(course_code)))
    # Load list of duplicate names
    print('\nLoading {}...'.format('Duplicate_Names_{}'.format(course_code)))
    duplicates = ft.load_headings('Duplicate_Names_{}'.format(course_code),
                                  'e')
    print('Loaded {}.'.format('Duplicate_Names_{}'.format(course_code)))
    # Load master file for course
    print('\nLoading {}...'.format('Master_Results_{}.csv'.format(
            course_code)))
    master_data = ft.load_csv('Master_Results_{}.csv'.format(course_code))
    print('Loaded {}.'.format('Master_Results_{}.csv'.format(course_code)))
    # Load Master headings file
    print('\nLoading {}...'.format('Master_Results_Headings_{}'.format
          (course_code)))
    master_headings = ft.load_headings('Master_Results_Headings_{}'.format
                                       (course_code), 'e')
    print('Loaded {}.'.format('Master_Results_Headings_{}'.format
          (course_code)))
    # Load Assessments headings file
    print('\nLoading {}...'.format('Assessment_Data_Headings.txt'))
    assessment_headings = ft.load_headings('Assessment_Data_Headings', 'e')
    print('Loaded {}.'.format('Assessment_Data_Headings.txt'))
     # Load assessment names file
    print('\nLoading {}...'.format('Assessment_Names_{}'.format(course_code)))
    assessments = ft.load_headings('Assessment_Names_{}'.format(course_code),
                                       'e')
    print('Loaded {}.'.format('Assessment_Names_{}'.format(course_code)))
    # Extract data for students on duplicates list and remove from assessments
    assessment_data = remove_duplicated(assessment_data, duplicates,
                                        course_code)
    # Add student and enrolment IDs and Course to assessment data
    assessment_data, unknown_names = db.add_ids(enrolments, assessment_data, 1)
    # Process unknown names so can be added manually or fixed and repeated
    process_unknown_names(unknown_names, course_code)
    # Place assessment_data into a DataFrame
    assessments_df = pd.DataFrame(data = assessment_data,
                                  columns = assessment_headings)
    # Check there are entries to process
    check_df(assessments_df)
    # Drop Unknown students so can be done manually
    assessments_df['EnrolmentID'] = assessments_df['EnrolmentID'].apply(
            ad.convert_to_nan, args=(['Unknown'],))
    assessments_df.dropna(subset=['EnrolmentID'], inplace=True)
    # Check there are entries to process
    check_df(assessments_df)
    # Drop non-assessment entries
    assessments_df['Grade item'] = assessments_df['Grade item'].apply(
            ad.convert_to_nan, args=(['Course total'],))
    assessments_df.dropna(subset=['Grade item'], inplace=True)
    # Check there are entries to process
    check_df(assessments_df)
    # Load assessment scores
    scores_name = get_score_name(course_code)
    print('\nLoading {}...'.format(scores_name))
    scores = ft.load_headings(scores_name, 'e')
    print('Loaded {}.'.format(scores_name))
    # Convert scores to ints
    scores = convert_scores(scores)
    # Create dictionary to hold passing scores for each assessment
    passing_scores = get_passing_scores(scores, assessments)
    # ad.debug_dict(passing_scores)
    # Convert Revised grades to a float (currently string)
    assessments_df['Revised grade'] = assessments_df['Revised grade'].apply(
            ad.convert_to_float)
    # Convert Revised grades to int (will round down to nearest whole number)
    assessments_df['Revised grade'] = assessments_df['Revised grade'].apply(
            ad.convert_to_int)
    # Drop entries that do not pass
    # Create a column to hold passing status of all entries
    assessments_df['Passing'] = assessments_df.apply(lambda x: check_scores(x
                  ['Revised grade'], x['Grade item'], passing_scores), axis=1)
    assessments_df.dropna(subset=['Passing'], inplace=True)
    # Check there are entries to process
    check_df(assessments_df)
    # Get just desired columns
    revised_headings = ['EnrolmentID', 'StudentID','Date and time', 'Name',
                        'Course', 'Grade item', 'Revised grade']
    assessments_df = assessments_df[revised_headings]
    # Date as Day Month Year from Date and Time
    assessments_df['Date and time'] = assessments_df['Date and time'].apply(
            extract_day_month_year)
    # Date as DD/MM/YYYY
    assessments_df['Date and time'] = assessments_df['Date and time'].apply(
            lambda x: pd.to_datetime(x).strftime('%d/%m/%Y'))
    # Dictionary storing assessment and Master Results headings for converting
    grades_dict = create_grades_dict(assessments, master_headings)
    # Convert Grade item to heading used in Master Results file
    assessments_df['Grade item'] = assessments_df['Grade item'].apply(
            convert_grade_item, args=(grades_dict,))
    # Convert Revised grade to 'Competent' as all grades are competent
    assessments_df['Revised grade'] = 'Competent'
    # Temp save to check
    '''
    assessments_df.to_csv('grade_revised_check_{}.csv'.format(
            ft.generate_time_string()), index=False)
    '''
    # Update Master Results File with Grade and Date
    updated_master = update_grades_res(master_data, assessments_df,
                                   master_headings)
    master_name = 'Master_Results_{}_'.format(course_code)
    # Save updated Master Results
    ft.save_list_csv(updated_master, master_headings, master_name)
    ft.process_warning_log(warnings, warnings_to_process)
    
    
if __name__ == '__main__':
    main() 