import csv
from typing import Dict, Union


class IO:

    def read(self, file: str) -> Dict[str, Union[str, bool]]:

        if file.endswith('.txt'):
            return self.__read(file, sep=':')
        elif file.endswith('.tsv') or file.endswith('.tab'):
            return self.__read(file, sep='\t')
        elif file.endswith('.csv'):
            return self.__read_csv(file)
        else:
            raise ValueError(f'Unknown file type: {file}')

    def __read(self, file: str, sep: str) -> Dict[str, Union[str, bool]]:
        ret = {}
        with open(file) as fh:
            for line_ in fh:
                line = line_.strip()
                if sep not in line:  # flag without value
                    line += sep
                key, val = line.split(sep)
                val = val.strip()
                if val == '':  # flag without value
                    val = True
                ret[key] = val
        return ret

    def __read_csv(self, file: str) -> Dict[str, Union[str, bool]]:
        """
        Use `csv` module to deal with quotes and commas in values
        """
        ret = {}
        with open(file) as fh:
            reader = csv.reader(fh)
            for row in reader:
                if len(row) == 1:
                    key, val = row[0], True
                else:
                    key, val = row[0:2]
                ret[key] = val
        return ret

    def write(self,
              parameters: Dict[str, Union[str, bool]],
              file: str):

        if file.endswith('.tsv') or file.endswith('.tab'):
            sep = '\t'
        elif file.endswith('.csv'):
            sep = ','
        else:  # pure txt format
            sep = ': '

        self.__write(parameters=parameters, file=file, sep=sep)

    def __write(
            self,
            parameters: Dict[str, Union[str, bool]],
            file: str,
            sep: str):

        with open(file, 'w') as fh:
            for key, val in parameters.items():
                if type(val) is bool:
                    if val:
                        fh.write(f'{key}\n')
                else:
                    if sep == ',' and ',' in val:  # use double quotes to protect commas
                        val = f'"{val}"'
                    fh.write(f'{key}{sep}{val}\n')
