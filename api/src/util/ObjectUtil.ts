import {StringUtil} from "./StringUtil";
import {TypeUtil} from "./TypeUtil";

/**
 * Utils for Object type
 */
export class ObjectUtil {

    /**
     * Property rename from camelCase to snake_case
     *
     * @param obj The object that you want to convert
     * @returns The object converted to snake_case
     */
    public static camelToSnake<T>(obj: T): T {
        if (TypeUtil.isScalarValue(obj)) {
            return obj;
        }

        const newObj = {} as T;
        Object.keys(obj).forEach(x => {

            if (x[0] === '_') {
                newObj[x] = obj[x];
                return newObj;
            }

            const name = x.split(/(?=[A-Z])/).join('_').toLowerCase();
            newObj[name] = obj[x];
        });

        return newObj;
    }

    /**
     * Deep property rename from camelCase to snake_case
     *
     * @param obj The object that you want to convert
     * @returns The object converted to snake_case
     */
    public static deepCamelToSnake<T>(obj: T): T {
        if (TypeUtil.isScalarValue(obj)) {
            return obj;
        }

        const newObj = {} as T;
        Object.keys(obj).forEach(x => {

            if (x[0] === '_') {
                newObj[x] = obj[x];
                return newObj;
            }

            const name = x.split(/(?=[A-Z])/).join('_').toLowerCase();

            if (Array.isArray(obj[x])) {
                //for empty arrays
                if (obj[x].length === 0) {
                    newObj[name] = obj[x];
                    return;
                }

                obj[x].forEach((x: T, key: number) => {
                    if (!newObj[name]) newObj[name] = [];
                    newObj[name][key] = ObjectUtil.deepCamelToSnake(x);
                });
            } else if (ObjectUtil.isObject(obj[x])) {
                newObj[name] = ObjectUtil.deepCamelToSnake(obj[x]);
            } else {
                newObj[name] = obj[x];
            }

        });

        return newObj;
    }

    /**
     * Property rename from snake_case to camelCase
     *
     * @param obj The object that you want to convert
     * @returns The object converted to camelCase
     */
    public static snakeToCamel<T>(obj: T): T {
        if (TypeUtil.isScalarValue(obj)) {
            return obj;
        }

        const newObj = {} as T;
        Object.keys(obj).forEach(x => {

            if (x[0] === '_') {
                newObj[x] = obj[x];
                return newObj;
            }

            const name = x.split('_').map((x, key) => key ?
                StringUtil.capitalize(x) : x).join('')

            newObj[name] = obj[x];
        });

        return newObj;
    }

    /**
     * Deep property rename from snake_case to camelCase
     *
     * @param obj The object that you want to convert
     * @returns The object converted to camelCase
     */
    public static deepSnakeToCamel<T>(obj: T): T {
        if (TypeUtil.isScalarValue(obj)) {
            return obj;
        }

        const newObj = {} as T;
        Object.keys(obj).forEach(x => {

            if (x[0] === '_') {
                newObj[x] = obj[x];
                return newObj;
            }

            const name = x.split('_').map((x, key) => key ?
                StringUtil.capitalize(x) : x).join('')

            if (Array.isArray(obj[x])) {
                newObj[name] = [];
                obj[x].forEach((x: T, _) => {
                    newObj[name].push(ObjectUtil.deepSnakeToCamel(x));
                });
            } else if (ObjectUtil.isObject(obj[x])) {
                newObj[name] = ObjectUtil.deepSnakeToCamel(obj[x]);
            } else {
                newObj[name] = obj[x];
            }
        });

        return newObj;
    }

    /**
     * Checks if the given value is object
     *
     * @param obj
     * @returns {boolean}
     */
    public static isObject(obj: object): boolean {
        return (typeof obj === "object" || typeof obj === 'function')
            && (obj !== null) && !(obj instanceof Date)
            && !(typeof obj['toHexString'] === 'function');
    }
}
