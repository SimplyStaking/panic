import { BaseChain } from "../interfaces/chains";
import { FilterState } from "../interfaces/filterState";

export const FilterStateAPI = {
    getFilterStates: getFilterStates,
    getFilterState: getFilterState
}

function getFilterStates(baseChains: BaseChain[]): FilterState[] {
    return baseChains.map(baseChain => ({
        chainName: baseChain.name,
        activeSeverities: [],
        lastClickedColumnIndex: 1,
        ordering: 'ascending'
    }));
}

function getFilterState(chainName: string, filterStates: FilterState[]): FilterState {
    return filterStates.find(filterState => filterState.chainName === chainName)
}