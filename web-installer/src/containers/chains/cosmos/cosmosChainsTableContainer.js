import { connect } from 'react-redux';
import CosmosChainsTable from '../../../components/chains/cosmos/tables/cosmosChainsTable';
import { removeConfig, loadConfig } from '../../../redux/actions/chainsActions';
import { changePage } from '../../../redux/actions/pageActions';

const mapStateToProps = (state) => ({
  cosmosConfigs: state.ChainsReducer.cosmosConfigs,
});

function mapDispatchToProps(dispatch) {
  return {
    pageChanger: (page) => dispatch(changePage(page)),
    removeConfigDetails: (details) => dispatch(removeConfig(details)),
    loadConfigDetails: (details) => dispatch(loadConfig(details)),
  };
}

const CosmosChainsTableContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(CosmosChainsTable);

export default CosmosChainsTableContainer;
