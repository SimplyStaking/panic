import {callFnWithTimeoutSafely} from "../../src/utils/timeout";

let timeout = 3000;
let params = [1, 2, 3];
let returnIfTimeoutExceeded = "Timeout exceeded";

describe('callFnWithTimeoutSafely', () => {
    it('calls callback fn and returns if timeout is not exceeded',
        async () => {
            let callback = jest.fn().mockImplementation(
                (..._) => {
                    return true;
                }
            );
            let ret = await callFnWithTimeoutSafely(
                callback, params, timeout, returnIfTimeoutExceeded
            );
            expect(ret).toBe(true);
            expect(callback).toHaveBeenCalledTimes(1);
            expect(callback).toHaveBeenCalledWith(1, 2, 3)
        });
    it('calls callback fn and raises exception if timeout exceeded',
        async () => {
            // In this test we will create a function whose execution time is
            // greater than the timeout.
            let timers: NodeJS.Timeout[] = [];
            const timer = (ms: any) => new Promise((res) => {
                timers.push(setTimeout(res, ms));
            });

            let callback = jest.fn().mockImplementation(
                async () => {
                    for (let i = 0; i < 3; i++) {
                        await timer(timeout);
                    }
                }
            );
            await expect(
                async () => {
                    await callFnWithTimeoutSafely(
                        callback, params, timeout, returnIfTimeoutExceeded
                    );
                }
            ).rejects.toThrow(Error);
            expect(callback).toHaveBeenCalledTimes(1);
            expect(callback).toHaveBeenCalledWith(1, 2, 3);

            // Clear all created timers to avoid memory leaks
            for (let timerObject of timers) {
                clearTimeout(timerObject)
            }
        });
});
