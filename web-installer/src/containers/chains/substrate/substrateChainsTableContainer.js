import { connect } from 'react-redux';
import SubstrateChainsTable from
  '../../../components/chains/substrate/tables/substrateChainsTable';
import { removeChainSubstrate, loadConfigSubstrate } from
  '../../../redux/actions/substrateActions';
import { changePage } from '../../../redux/actions/pageActions';

// We will need the configured state of the substrate nodes
const mapStateToProps = (state) => ({
  config: state.SubstrateChainsReducer,
});

// Functions required are to change page, remove the chain details
// later to also load the chain details.
function mapDispatchToProps(dispatch) {
  return {
    pageChanger: (page) => dispatch(changePage(page)),
    removeChainDetails: (details) => dispatch(removeChainSubstrate(details)),
    loadConfigDetails: (details) => dispatch(loadConfigSubstrate(details)),
  };
}

const SubstrateChainsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(SubstrateChainsTable);

export default SubstrateChainsTableContainer;
