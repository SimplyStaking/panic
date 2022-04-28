import {BaseChain} from "../interfaces/chains";
import {FilterState} from "../interfaces/filterState";

export const FilterStateAPI = {
    getFilterStates: getFilterStates,
    getFilterState: getFilterState
}

/**
 * Returns an array of filter states based on an array of base chains and previous filter states.
 * @param baseChains base chains to be used as reference.
 * @param filterStates previous filter states to be used as reference.
 * @returns array of updated {@link FilterState} objects.
 */
function getFilterStates(baseChains: BaseChain[], filterStates: FilterState[]): FilterState[] {
    return baseChains.map(baseChain => ({
        chainName: baseChain.name,
        selectedSubChains: filterStates.some(filterState => filterState.chainName === baseChain.name) ?
            filterStates.filter(filterState => filterState.chainName === baseChain.name)[0].selectedSubChains : [],
        selectedSeverities: filterStates.some(filterState => filterState.chainName === baseChain.name) ?
            filterStates.filter(filterState => filterState.chainName === baseChain.name)[0].selectedSeverities : []
    }));
}

/**
 * Returns a filter state based on a chain name.
 * @param chainName chain name which should match the filter state.
 * @param filterStates array of filter states to be checked.
 * @returns a {@link FilterState} object.
 */
function getFilterState(chainName: string, filterStates: FilterState[]): FilterState {
    return filterStates.find(filterState => filterState.chainName === chainName);
}
