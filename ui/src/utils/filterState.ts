import {BaseChain} from "../interfaces/chains";
import {FilterState} from "../interfaces/filterState";

export const FilterStateAPI = {
    getFilterStates: getFilterStates,
    getFilterState: getFilterState
}

/**
 * Returns an array of filter states based on an array of base chains.
 * @param baseChains base chains to be used as reference.
 * @returns array of {@link FilterState} objects.
 */
function getFilterStates(baseChains: BaseChain[]): FilterState[] {
    return baseChains.map(baseChain => ({
        chainName: baseChain.name,
        selectedSubChains: [],
        selectedSeverities: []
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
