/**
 * Utils for Types
 */
export class TypeUtil {
    /**
     * Check if is scalar value
     * 
     * @param value Any value to check
     */
    public static isScalarValue(value: any): boolean {
        const types = ['string', 'boolean', 'number', 'undefined', null];
        return types.some(x => typeof value === x || value === x);
    }
}