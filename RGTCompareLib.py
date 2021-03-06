# -*- coding: utf-8 -*-

#
#   为RGT测试提供封装，内部调用CompareLib.py实现。
#

import os
import CSVLib
import CompareLib
import filecmp
import re
import CommonLib

def IsContainSubStr(String, SubStr):
    return String.find(SubStr) != -1

def BothContainSubStr(String1, String2, SubStr):
    if String1.find(SubStr) != -1 and String2.find(SubStr) != -1:
        return True
    else:
        return False

#
#   Expected:       保存期待.csv的目录
#   Test:           保存测试.csv的目录
#   SaveFilePath:   保存比较结果的目录
#
def CompareOneCaseCSV(Expected,Test,SaveFilePath):
    CSVFile1 = CSVLib.GetCSVFiles(Expected)
    CSVFile2 = CSVLib.GetCSVFiles(Test)
    fd = open(SaveFilePath, 'w')

    if len(CSVFile1) == 0 and len(CSVFile2) == 0:
        fd.write("Both no csv")
    elif len(CSVFile1) == 0 and len(CSVFile2) != 0:
        fd.write("Expected no csv")
    elif len(CSVFile1) != 0 and len(CSVFile2) == 0:
        fd.write("Test no csv")
    else:
        fd.close()
        #
        #   默认RGT的每个Test Case中只生成1个.csv文件。
        #
        assert(len(CSVFile1) == 1 and len(CSVFile2) == 1)
        CompareLib.DoCompareCSV(CSVFile1.get(CSVFile1.keys()[0]),
                                CSVFile2.get(CSVFile2.keys()[0]),
                                SaveFilePath)
    fd.close()

def CompareGenerateAtString(ExptString, TestString):
    FixStringAt = [
        'Configuration Settings Report generated at',
        'Platform Inventory Report generated at',
        'Firmware Inventory Report generated at',
        'Flash Layout Report generated at',
    ]
    for string in FixStringAt:
        Index1 = ExptString.find(string)
        Index2 = ExptString.find('for project')
        if Index1 != -1 and Index2 != -1:
            pattern = re.compile(ExptString[:len(string)] + ' .*\.csv ' + ExptString[Index2:])
            if pattern.match(TestString) != None:
                return True
    return False

def CompareNoAtString(ExptString, TestString):
    FixString = [
        'Configuration Settings Report',
        'Platform Inventory Report',
        'Firmware Inventory Report',
        'Flash Layout Report',
    ]
    for string in FixString:
        Index1 = ExptString.find(string)
        if Index1 != -1:
            pattern = re.compile(ExptString[:len(string)] + ', .*, .*\.csv')
            if pattern.match(TestString) != None:
                return True
    return False

#
#   ExpectedLogPath:    期待log文件
#   TestLogPath:        测试log文件
#   LogSavePath:        保存结果文件
#   
#   ExpectedLog always save as windows type.
#
def CompareOneCaseLog(ExpectedLogPath,TestLogPath,LogSavePath):
    fd = open(LogSavePath, 'w')

    #
    #   期待不存在或者内容为空，直接略过。
    #
    if not os.path.isfile(ExpectedLogPath) or \
        (
            os.path.getsize(ExpectedLogPath) == 0 and
            os.path.getsize(TestLogPath) != 0
        ):
        fd.write('[Skip]')
        fd.close()
        return

    #
    #   测试的log如果不存在则表示RGT运行错误，需要查看。
    #
    if not os.path.isfile(TestLogPath) or not os.path.isfile(TestLogPath):
        fd.write('[Error]')
        fd.close()
        return

    ExpectedString = CommonLib.ReadFile(ExpectedLogPath)
    TestLogString = CommonLib.ReadFile(TestLogPath)

    ExpectedString = CommonLib.ConvertAndStripString(ExpectedString)
    TestLogString = CommonLib.ConvertAndStripString(TestLogString)

    #
    #   试图比较正确的log信息。
    #
    if ExpectedString == TestLogString:
        fd.write('[True]')
        fd.close()
        return

    #
    #   如果只有一行log信息的话，那么应该只有路径不一样。
    #   如果存在多行log信息的话，我们只比较最后一行信息。
    #
    ExptOneLineString = ''
    TestOneLineString = ''
    if len(ExpectedString.split('\n')) == 1 and len(TestLogString.split('\n')) == 1:
        ExptOneLineString = ExpectedString
        TestOneLineString = TestLogString
    else:
        ExptOneLineString = ExpectedString.split('\n')[-1]
        TestOneLineString = TestLogString.split('\n')[-1]

    if CompareGenerateAtString(ExptOneLineString, TestOneLineString) or CompareNoAtString(ExptOneLineString, TestOneLineString):
        fd.write('[True]')
        fd.close()
        return

    #
    #   special case.
    #
    if BothContainSubStr(ExpectedString, TestLogString, 'Error: 1: The Report specified was not found.'):
        fd.write('[#True#]')
        fd.close()
        return

    fd.write('[False]')
    fd.close()

#
#   查看CSV和log的比较结果。
#
def CheckCompareResult(CSVResultPath,LogResultPath,ExceptionContentList):
    #
    #   CSVResultPath中保存的是比较csv的内容。
    #
    String1 = CommonLib.ReadFile(CSVResultPath)

    if String1 == '':
        StringToReturn = '[True]'
    else:
        if String1 == 'Both no csv':
            StringToReturn = '[True]'
        elif String1 == 'Expected no csv':
            StringToReturn = '[Fix]'
        elif String1 == 'Test no csv':
            StringToReturn = '[Error]'
        #
        #   Exception
        #
        elif String1 in ExceptionContentList:
            StringToReturn = '[True]'
        else:
            StringToReturn = '[Check]'
    return StringToReturn + '\t' + CommonLib.ReadFile(LogResultPath)

#
#   1. 比较CSV文件
#   2. 比较Log文件
#   3. 检查比较结果
#
#   Param1 : 测试用例路径
#   Param2 : 期待目录路径
#   Param3 : 测试目录路径
#   Param4 : 期待log文件名
#   Param5 : 测试log文件名
#   Param6 : 保存对比csv结果路径
#   Param7 : 保存对比log结果路径
def CompareOneCase(ExpectedPath, TestPath, ExpLogFileName, TestLogFileName, CSVSavePath, LogSavePath, ExceptionContentList):
    CompareOneCaseCSV(ExpectedPath, TestPath, CSVSavePath)
    CompareOneCaseLog(os.path.join(ExpectedPath,ExpLogFileName),
                      os.path.join(TestPath,TestLogFileName),
                      LogSavePath)

    return list((os.path.dirname(ExpectedPath) + '\t' + CheckCompareResult(CSVSavePath,LogSavePath,ExceptionContentList)).split('\t'))