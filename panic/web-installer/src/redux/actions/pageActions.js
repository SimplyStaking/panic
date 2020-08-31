import { CHANGE_PAGE}  from "./types";

export function changePage(payload) {
    return {
        type: CHANGE_PAGE,
        payload
    }
}