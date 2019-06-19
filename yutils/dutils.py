#
#
#
import time
import datetime
import calendar

#
#    well...
#
secondsinday      = time.mktime( (2000, 0, 1, 0, 0, 0, 0, 0, 0) ) - time.mktime( (2000, 0, 0, 0, 0, 0, 0, 0, 0) )
defaultfakeyear   = 2000

#
#
#
def yyyymmdd_from_datetimedate(datetimedate):
    """
    instantiate yyyymmdd day string from datetime.date object
    """
    return "%04d%02d%02d" % (datetimedate.year, datetimedate.month, datetimedate.day)

#
#
#
def iyear_imonth_from_yyyymm(yyyymm):
    """
    extract (int year, int month) tuple from yyyymm string or integer
    """
    szyyyymm = str(int(yyyymm))
    if 6 != len(szyyyymm)           : raise ValueError
    iyear = int(szyyyymm[:-2])
    if iyear < 1950 or iyear > 2049 : raise ValueError
    imonth = int(szyyyymm[4:])
    if imonth < 1 or imonth > 12    : raise ValueError
    return (iyear, imonth)

#
#
#
def yyyymm_from_iyear_imonth(year, month):
    """
    """
    iyear = int(year)
    if iyear < 1950 or iyear > 2049 : raise ValueError
    imonth = int(month)
    if imonth < 1 or imonth > 12    : raise ValueError
    return "%04d%02d" % (iyear, imonth)
#
#
#
def iyear_imonth_nextmonth_of_yyyymm(yyyymm):
    """
    extract (int year, int month) tuple for 'next month' from yyyymm string or integer
    """
    iyear, imonth = iyear_imonth_from_yyyymm(yyyymm)
    inextmonth = imonth + 1 if imonth < 12 else 1
    inextyear  = iyear      if imonth < 12 else iyear + 1
    return (inextyear, inextmonth)

#
#
#
def iyear_imonth_iday_from_yyyymmdd(yyyymmdd):
    """
    extract (int year, int month, int day) tuple from yyyymmdd string or integer
    (since only years in range [1950,2049] are considered relevant, there cannot be (missing) leading zeros 
    """
    szyyyymmdd = str(int(yyyymmdd))
    if 8 != len(szyyyymmdd)         : raise ValueError
    iyear  = int(szyyyymmdd[:-4])
    if iyear < 1950 or iyear > 2049 : raise ValueError
    imonth = int(szyyyymmdd[4:6])
    if imonth < 1 or imonth > 12    : raise ValueError
    iday   = int(szyyyymmdd[6:])
    if iday   < 1    or iday   > calendar.monthrange(iyear, imonth)[1]: raise ValueError
    return (iyear, imonth, iday)

#
#
#
def yyyymmdd_from_iyear_imonth_iday(year, month, day):
    """
    yyyymmdd string from (year, month, day) integers or strings
    """
    iyear  = int(year)
    if iyear < 1950 or iyear > 2049 : raise ValueError
    imonth = int(month)
    if imonth < 1 or imonth > 12    : raise ValueError
    iday   = int(day)
    if iday < 1 or iday > calendar.monthrange(iyear, imonth)[1]: raise ValueError
    return "%04d%02d%02d" %  (iyear, imonth, iday)

#
#
#
def idays_in_month_yyyymm(yyyymm):
    """
    number of days in 'month' from yyyymm string or integer
    """
    iyear, imonth = iyear_imonth_from_yyyymm(yyyymm)
    return calendar.monthrange(iyear, imonth)[1]

#
#
#
def ihour_iminute_isecond_from_hhmmss(szhhmmss):
    """
    extract (int hour, int minute, int second) tuple from hhmmss string
    """
    if 6 != len(szhhmmss) :      raise ValueError
    ihour = int(szhhmmss[:2])
    if ihour < 0 or ihour > 23 : raise ValueError
    imin = int(szhhmmss[2:4])
    if imin < 0 or imin > 59 :   raise ValueError
    isec = int(szhhmmss[4:6])
    if isec < 0 or isec > 59 :   raise ValueError
    return (ihour, imin, isec)

#
#
#
def datetime_start_of_month_yyyymm(yyyymm, hhmmss = None):
    """
    optional hhmmss gives the offset of day 1 (e.g. start at noon iso 00:00:00)
    """
    iyear, imonth = iyear_imonth_from_yyyymm(yyyymm)
    
    if hhmmss is None:
        return datetime.datetime(iyear, imonth, 1)
    
    ihour, imin, isec = ihour_iminute_isecond_from_hhmmss(hhmmss)    
    return datetime.datetime(iyear, imonth, 1, ihour, imin, isec)

#
#
#
def iseconds_since_epoch_start_of_month_yyyymm(yyyymm, hhmmss = None):
    """
    optional hhmmss gives the offset of day 1 (e.g. start at noon iso 00:00:00)
    """
    iyear, imonth = iyear_imonth_from_yyyymm(yyyymm)
    
    if hhmmss is None:
        return int( time.mktime((iyear, imonth, 1, 0, 0, 0, 0, 0, 0)) ) 

    ihour, imin, isec = ihour_iminute_isecond_from_hhmmss(hhmmss)    
    return int( time.mktime((iyear, imonth, 1, ihour, imin, isec, 0, 0, 0)) )

#
#
#
def datetime_start_of_nextmonth_yyyymm(yyyymm, hhmmss = None):
    """
    optional hhmmss gives the offset of day 1 (e.g. start at noon iso 00:00:00)
    """
    inextyear, inextmonth = iyear_imonth_nextmonth_of_yyyymm(yyyymm)
    
    if hhmmss is None:
        return datetime.datetime(inextyear, inextmonth, 1)
    
    ihour, imin, isec = ihour_iminute_isecond_from_hhmmss(hhmmss)    
    return datetime.datetime(inextyear, inextmonth, 1, ihour, imin, isec)

#
#
#
def iseconds_since_epoch_start_of_nextmonth_yyyymm(yyyymm, hhmmss = None):
    """
    optional hhmmss gives the offset of day 1 (e.g. start at noon iso 00:00:00)
    """
    iyear, imonth = iyear_imonth_nextmonth_of_yyyymm(yyyymm)
    
    if hhmmss is None:
        return int(time.mktime((iyear, imonth, 1, 0, 0, 0, 0, 0, 0))) 

    ihour, imin, isec = ihour_iminute_isecond_from_hhmmss(hhmmss)    
    return int(time.mktime((iyear, imonth, 1, ihour, imin, isec, 0, 0, 0))) 

#
#
#
def yyyymm_nextmonth_of_yyyymm(yyyymm):
    """
    yyyymm string for 'next month' from yyyymm string or integer
    """
    inextyear, inextmonth = iyear_imonth_nextmonth_of_yyyymm(yyyymm)
    return "%04d%02d" % (inextyear, inextmonth)

#
#
#
def date_of_yyyymmdd(yyyymmdd):
    """
    instantiate datetime.date object for yyyymmdd day string or int
    """
    iyear, imonth, iday = iyear_imonth_iday_from_yyyymmdd(yyyymmdd)
    return datetime.date(iyear, imonth, iday)

#
#
#
def datetime_of_yyyymmdd(yyyymmdd, hhmmss=None):
    """
    instantiate datetime.date object for yyyymmdd day string or int
    optional hhmmss gives the offset of day 1 (e.g. start at noon iso 00:00:00)
    """
    iyear, imonth, iday = iyear_imonth_iday_from_yyyymmdd(yyyymmdd)

    if hhmmss is None:
        return datetime.datetime(iyear, imonth, iday)
    
    ihour, imin, isec = ihour_iminute_isecond_from_hhmmss(hhmmss)    
    return datetime.datetime(iyear, imonth, iday, ihour, imin, isec)

#
#
#
def iseconds_since_epoch_of_yyyymmdd(yyyymmdd, hhmmss=None):
    """
    """
    iyear, imonth, iday = iyear_imonth_iday_from_yyyymmdd(yyyymmdd)

    if hhmmss is None:
        return int(time.mktime((iyear, imonth, iday, 0, 0, 0, 0, 0, 0))) 
    
    ihour, imin, isec = ihour_iminute_isecond_from_hhmmss(hhmmss)    
    return int(time.mktime((iyear, imonth, iday, ihour, imin, isec, 0, 0, 0)))
   
#
#
#
def yyyymmdd_first_day_of_yyyymm(yyyymm):
    """
    instantiate yyyymmdd day string for the first day of the input yyyymm month string or int
    """
    iyear, imonth = iyear_imonth_from_yyyymm(yyyymm)
    return "%04d%02d01" % (iyear, imonth)

#
#
#
def yyyymmdd_last_day_of_yyyymm(yyyymm):
    """
    instantiate yyyymmdd day string for the last day of the input yyyymm month string or int
    """
    iyear, imonth = iyear_imonth_from_yyyymm(yyyymm)
    iday = calendar.monthrange(iyear, imonth)[1]
    return "%04d%02d%02d" % (iyear, imonth, iday)

#
#
#
def yyyymmdd_idays_before_yyyymmdd(yyyymmdd, idays):
    """
    instantiate yyyymmdd day string, idays earlier than input yyyymmdd day string 
    """
    if idays < 0 : return yyyymmdd_idays_after_yyyymmdd(yyyymmdd, -idays)
    return yyyymmdd_from_datetimedate( date_of_yyyymmdd(yyyymmdd) + datetime.timedelta(days=-idays) )
    
#
#
#
def yyyymmdd_idays_after_yyyymmdd(yyyymmdd, idays):
    """
    instantiate yyyymmdd day string, idays later than input yyyymmdd day string 
    """
    if idays < 0 : return yyyymmdd_idays_before_yyyymmdd(yyyymmdd, -idays)
    return yyyymmdd_from_datetimedate( date_of_yyyymmdd(yyyymmdd) + datetime.timedelta(days=idays) )

#
#
#
def yyyymmdd_idays_before_yyyymm(yyyymm, idays):
    """
    instantiate yyyymmdd day string, idays earlier than FIRST day of the input yyyymm month string
    """
    #if idays < 0 : raise ValueError  
    #if idays < 0 : return yyyymmdd_idays_after_yyyymm(yyyymm, -idays)
    if idays < 0 : return yyyymmdd_first_day_of_yyyymm(yyyymm)
    return yyyymmdd_from_datetimedate( date_of_yyyymmdd(yyyymmdd_first_day_of_yyyymm(yyyymm)) + datetime.timedelta(days=-idays) )

#
#
#
def yyyymmdd_idays_after_yyyymm(yyyymm, idays):
    """
    instantiate yyyymmdd day string, idays later than LAST day of the input yyyymm month string
    """
    #if idays < 0 : raise ValueError  
    #if idays < 0 : return yyyymmdd_idays_before_yyyymm(yyyymm, -idays)
    if idays < 0 : yyyymmdd_last_day_of_yyyymm(yyyymm)
    return yyyymmdd_from_datetimedate( date_of_yyyymmdd(yyyymmdd_last_day_of_yyyymm(yyyymm)) + datetime.timedelta(days=idays) )       
#
#
#
def g_yyyymm_in_yyyy(yyyy):
    """
    generate all yyyymm month strings for yyyy year string or int
    """
    iyear = int(yyyy)
    if iyear < 1950 or iyear > 2049 : raise ValueError
    for imonth in range(1,13) :
        yield str(iyear * 100 + imonth) 

#
#
#
def g_yyyymmdd_in_yyyymm(yyyymm):
    """
    generate all yyyymmdd day strings for yyyymm month string or int
    """
    iyear, imonth = iyear_imonth_from_yyyymm(yyyymm)
    for iday in range(1, calendar.monthrange(iyear, imonth)[1] + 1) :
        yield str(iyear * 10000 + imonth * 100 + iday) 

#
#
#
def g_yyyymmdd_in_yyyy(yyyy):
    """
    generate all yyyymmdd day strings for yyyy year string or int
    """
    iyear = int(yyyy)
    if iyear < 1950 or iyear > 2049 : raise ValueError
    for yyyymm in g_yyyymm_in_yyyy(yyyy):
        for yyyymmdd in g_yyyymmdd_in_yyyymm(yyyymm):
            yield yyyymmdd

#
#
#
def g_yyyymmdd_interval(yyyymmddfirst, yyyymmddlast):
    """
    generate all yyyymmdd day strings from yyyymmddfirst till yyyymmddlast - INCLUDING the first and last bounds
    """
    date_yyyymmddfirst = date_of_yyyymmdd(yyyymmddfirst)
    date_yyyymmddlast  = date_of_yyyymmdd(yyyymmddlast)

    isize = 1 + abs( (date_yyyymmddlast - date_yyyymmddfirst).days )

    step_days = 1 if date_yyyymmddfirst < date_yyyymmddlast else -1

    for idx in range(isize) :
        yield yyyymmdd_from_datetimedate(date_yyyymmddfirst + datetime.timedelta(days=idx*step_days))


####################
#                  #
#    MM & MMDD     #
#                  #
####################

#
#
#
#
def iyyyy_from_yyyy(yyyy):
    """
    extract (int) year from yyyy string or integer
    """
    iyear = int(yyyy)
    if iyear < 1950 or iyear > 2049 : raise ValueError
    return iyear

#
#
#
def mmdd_from_datetimedate(datetimedate):
    """
    instantiate mmdd day string from datetime.date object
    """
    return "%02d%02d" % (datetimedate.month, datetimedate.day)

#
#
#
def imonth_from_mm(mm):
    """
    extract int month from mm string or integer
    """
    szmm = str(int(mm))
    if len(szmm) not in (1,2)       : raise ValueError
    imonth = int(mm)
    if imonth < 1 or imonth > 12    : raise ValueError
    return imonth
#
#
#
def imonth_iday_from_mmdd(mmdd, fakeyyyy=defaultfakeyear):
    """
    extract (int month, int day) tuple from mmdd string or integer
    """
    szmmdd = str(int(mmdd))
    if len(szmmdd) not in (3,4)     : raise ValueError
    imonth = int(mmdd[:-2])
    if imonth < 1 or imonth > 12    : raise ValueError
    if len(szmmdd) == 3 : iday = int(szmmdd[1:])
    else:                 iday = int(szmmdd[2:])
    
    if fakeyyyy is None : fakeyyyy = defaultfakeyear
    ifakeyyyy = iyyyy_from_yyyy(fakeyyyy)
    if iday < 1 or iday > calendar.monthrange(ifakeyyyy, imonth)[1]: raise ValueError( " day in month %s must be 1 <= day <= %s" % (imonth, calendar.monthrange(ifakeyyyy, imonth)[1]))

    return (imonth, iday)

#
#
#
def mmdd_from_imonth_iday(month, day, fakeyyyy=defaultfakeyear):
    """
    """
    imonth = int(month)
    if imonth < 1 or imonth > 12    : raise ValueError
    iday = int(day)
    if fakeyyyy is None : fakeyyyy = defaultfakeyear
    ifakeyyyy = iyyyy_from_yyyy(fakeyyyy)
    if iday < 1 or iday > calendar.monthrange(ifakeyyyy, imonth)[1]: raise ValueError( " day in month %s must be 1 <= day <= %s" % (imonth, calendar.monthrange(ifakeyyyy, imonth)[1]))

    return "%02d%02d" % (imonth, iday)


#
#
#
def fake_date_of_mmdd(mmdd, fakeyyyy=defaultfakeyear):
    """
    instantiate datetime.date object for mmdd day string or int in specified fake year
    """
    imonth, iday = imonth_iday_from_mmdd(mmdd, fakeyyyy)
    if fakeyyyy is None : fakeyyyy = defaultfakeyear
    ifakeyear = iyyyy_from_yyyy(fakeyyyy)
    return datetime.date(ifakeyear, imonth, iday)

