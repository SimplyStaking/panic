export function capitalizeFirstLetter(string: string): string {
    if (!string || string.length == 0) {
        return string;
    }

    return string.charAt(0).toUpperCase() + string.slice(1);
}