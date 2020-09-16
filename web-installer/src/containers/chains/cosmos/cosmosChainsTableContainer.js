import { connect } from 'react-redux';
import CosmosChainsTable from '../../../components/chains/cosmos/tables/cosmosChainsTable';
import { removeConfigCosmos, loadConfigCosmos } from '../../../redux/actions/cosmosChainsActions';
import { changePage } from '../../../redux/actions/pageActions';

const mapStateToProps = (state) => ({
  cosmosConfigs: state.CosmosChainsReducer.cosmosConfigs,
});

function mapDispatchToProps(dispatch) {
  return {
    pageChanger: (page) => dispatch(changePage(page)),
    removeConfigDetails: (details) => dispatch(removeConfigCosmos(details)),
    loadConfigDetails: (details) => dispatch(loadConfigCosmos(details)),
  };
}

const CosmosChainsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(CosmosChainsTable);

export default CosmosChainsTableContainer;
