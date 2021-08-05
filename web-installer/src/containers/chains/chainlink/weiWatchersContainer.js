import { withFormik } from 'formik';
import { connect } from 'react-redux';
import WeiWatchersForm from 'components/chains/chainlink/forms/weiWatchersForm';
import { addWeiWatchers } from 'redux/actions/chainlinkActions';
import ChainlinkData from 'data/chainlink';

const Form = withFormik({
  mapPropsToValues: () => ({
    name: '',
    weiwatchers_url: '',
    monitor_contracts: true,
  }),
})(WeiWatchersForm);

// ------------------------- WeiWatchers Data --------------------

// Redux data that will be used to control the node form.
const mapStateToProps = (state) => ({
  currentChain: state.CurrentChainlinkChain,
  chainConfig: state.ChainlinkChainsReducer,
  chainlinkNodesConfig: state.ChainlinkNodesReducer,
  cosmosNodesConfig: state.CosmosNodesReducer,
  substrateNodesConfig: state.SubstrateNodesReducer,
  reposConfig: state.GitHubRepositoryReducer,
  systemConfig: state.SystemsReducer,
  dockerHubConfig: state.DockerHubReducer,
  data: ChainlinkData,
});

// Functions to be used in the WeiWatchers form to save the form's details
function mapDispatchToProps(dispatch) {
  return {
    saveWeiWatchersDetails: (details) => dispatch(addWeiWatchers(details)),
  };
}

// Combine state and dispatch functions to the form
const WeiWatchersFormContainer = connect(mapStateToProps, mapDispatchToProps)(Form);

export default WeiWatchersFormContainer;
