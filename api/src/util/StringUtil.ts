/**
 * Utils for String type
 */
export class StringUtil {
    public static capitalize(str: string): string {
        const lower = str.toLocaleLowerCase();
        return str.charAt(0).toUpperCase() + lower.slice(1);
    }

    public static trim(str: string): string {
        return str ? str.trim() : str;
    }
}