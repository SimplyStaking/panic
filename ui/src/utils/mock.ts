export const mockImplementationOnceResolveHandler = (responseData: any) => {
    Promise.resolve({ json: () => Promise.resolve(responseData) });
}