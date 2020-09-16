import { connect } from 'react-redux';
import SubstrateChainsTable from '../../../components/chains/substrate/tables/substrateChainsTable';
import { removeConfigSubstrate, loadConfigSubstrate } from '../../../redux/actions/substrateChainsActions';
import { changePage } from '../../../redux/actions/pageActions';

const mapStateToProps = (state) => ({
  substrateConfigs: state.SubstrateChainsReducer.substrateConfigs,
});

function mapDispatchToProps(dispatch) {
  return {
    pageChanger: (page) => dispatch(changePage(page)),
    removeConfigDetails: (details) => dispatch(removeConfigSubstrate(details)),
    loadConfigDetails: (details) => dispatch(loadConfigSubstrate(details)),
  };
}

const SubstrateChainsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(SubstrateChainsTable);

export default SubstrateChainsTableContainer;
