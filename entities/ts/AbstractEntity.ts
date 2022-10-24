/**
 * Abstract Entity for common functions.
 */
export abstract class AbstractEntity {
    public static fromJSON(json: Object, className: any): any {
        // using "reflection" to create instances of className
        const model = Reflect.construct(className, []);

        Object.keys(json).forEach((attr: string) => {
            model[`_${attr}`] = json[attr];
        });

        return model;
    }
}
