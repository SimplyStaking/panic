import { BaseChain } from "../interfaces/chains";
import { FilterState } from "../interfaces/filterState";
import { SeverityAPI } from "./severity";

export const FilterStateAPI = {
    getFilterStates: getFilterStates,
    getFilterState: getFilterState
}

function getFilterStates(baseChains: BaseChain[]): FilterState[] {
    return baseChains.map(baseChain => ({
        chainName: baseChain.name,
        selectedSeverities: SeverityAPI.getAllSeverityValues(true),
        lastClickedColumnIndex: 1,
        ordering: 'descending'
    }));
}

function getFilterState(chainName: string, filterStates: FilterState[]): FilterState {
    return filterStates.find(filterState => filterState.chainName === chainName)
}
