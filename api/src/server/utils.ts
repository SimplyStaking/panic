// These functions wrap a result or an error as an object

export const resultJson = (result: any) => ({result});
export const errorJson = (error: any) => ({error});

// Transforms a string representing a boolean as a boolean
export const toBool = (boolStr: string): boolean => ['true', 'yes', 'y'].some(
    (element) => boolStr.toLowerCase().includes(element));

// Checks which keys have values which are missing (null, undefined) in
// a given object and returns an array of keys having missing values.
export const missingValues = (object: { [id: string]: any }): string[] => {
    let missingValuesList: string[] = [];
    Object.keys(object).forEach((key) => {
        if (object[key] == null || object[key] == undefined) {
            missingValuesList.push(key);
        }
    });
    return missingValuesList;
};

export const allElementsInList = (elements: any[], list: any[]): boolean => {
    const resultList: boolean[] = elements.map((element: any): boolean => {
        return list.includes(element)
    });
    return resultList.every(Boolean);
};

export const getElementsNotInList = (elements: any[], list: any[]): any[] => {
    return elements.filter(element => !list.includes(element));
};

export const allElementsInListHaveTypeString = (list: any[]): boolean => {
    return list.every(item => typeof (item) === "string")
};

export const getPrometheusMetricFromBaseChain = (baseChain: string): string => {
    switch (baseChain.toLowerCase()) {
        case 'cosmos':
            return 'tendermint_consensus_height'
        case 'chainlink':
            return 'max_unconfirmed_blocks'
        default:
            return ''
    }
}

export const verifyPrometheusPing = (prometheusPingData: string, baseChain: string): boolean => {
    const metric = getPrometheusMetricFromBaseChain(baseChain);
    let isValid: boolean = false;
    prometheusPingData.split('\n').forEach((line) => {
        if (!isValid) {
            line.split(' ').forEach(token => {
                if (!isValid && token.includes(metric)) {
                    isValid = true;
                }
            })
        }
    });
    return isValid;
}

export const verifyNodeExporterPing = (nodeExporterPingData: string): boolean => {
    let isValid: boolean = false;
    nodeExporterPingData.split('\n').forEach((line) => {
        if (!isValid) {
            line.split(' ').forEach(token => {
                if (!isValid && token === 'node_cpu_seconds_total') {
                    isValid = true;
                }
            })
        }
    });
    return isValid;
}

export const fulfillWithTimeLimit = async (task: Promise<any>, timeLimit: number, failureValue: any = null) => {
    let timeout;
    const timeoutPromise = new Promise((resolve, _reject) => {
        timeout = setTimeout(() => {
            resolve(failureValue);
        }, timeLimit);
    });
    const response = await Promise.race([task, timeoutPromise]);
    if (timeout) {
        clearTimeout(timeout);
    }
    return response;
}
