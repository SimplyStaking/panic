import { connect } from 'react-redux';
import CosmosChainsTable from '../../../components/chains/cosmos/tables/cosmosChainsTable';
import { removeChainCosmos, loadConfigCosmos } from '../../../redux/actions/cosmosChainsActions';
import { changePage } from '../../../redux/actions/pageActions';

const mapStateToProps = (state) => ({
  config: state.CosmosChainsReducer,
});

function mapDispatchToProps(dispatch) {
  return {
    pageChanger: (page) => dispatch(changePage(page)),
    removeChainDetails: (details) => dispatch(removeChainCosmos(details)),
    loadConfigDetails: (details) => dispatch(loadConfigCosmos(details)),
  };
}

const CosmosChainsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(CosmosChainsTable);

export default CosmosChainsTableContainer;
