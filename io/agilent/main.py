from gcms_result import GcmsResult
from gcms_data import GcmsData


if __name__ == '__main__':

    result = GcmsResult('../../data/FA03.D/RESULTS.csv')
    result = GcmsData('../../data/FA03.D/DATA.MS')
    print(result.data.head())


    