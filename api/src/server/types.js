"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isAlertsOverviewInput = void 0;
var utils_1 = require("./utils");
function isAlertsOverviewInput(object) {
    var isAlertsOverviewInput = true;
    if (!object || object.constructor !== Object) {
        return false;
    }
    Object.keys(object).forEach(function (key, _) {
        if (!(object[key] && object[key].constructor === Object)) {
            isAlertsOverviewInput = false;
        }
        else if (!('systems' in object[key] && 'repos' in object[key])) {
            isAlertsOverviewInput = false;
        }
        else if (!(Array.isArray(object[key].systems)
            && Array.isArray(object[key].repos))) {
            isAlertsOverviewInput = false;
        }
        else if (!(utils_1.allElementsInListHaveTypeString(object[key].systems)
            && utils_1.allElementsInListHaveTypeString(object[key].repos))) {
            isAlertsOverviewInput = false;
        }
    });
    return isAlertsOverviewInput;
}
exports.isAlertsOverviewInput = isAlertsOverviewInput;
