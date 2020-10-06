import { withFormik } from 'formik';
import { connect } from 'react-redux';
import ChainForm from '../../../components/chains/cosmos/forms/chainForm';
import {
  addChainCosmos, updateChainCosmos, resetCurrentChainId,
} from '../../../redux/actions/cosmosActions';
import { changeStep, changePage } from '../../../redux/actions/pageActions';
import ChainSchema from './schemas/chainSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    chainName: '',
  }),
  mapPropsToValues: () => ({
    chainName: '',
  }),
  validationSchema: (props) => ChainSchema(props),
})(ChainForm);

const mapStateToProps = (state) => ({
  step: state.ChangeStepReducer.step,
  config: state.CosmosChainsReducer,
  currentChain: state.CurrentCosmosChain,
});

// step and page changers are used diretly in this form instead of their
// respective button containers as extra functionality is needed for the
// onSubmit events.
function mapDispatchToProps(dispatch) {
  return {
    saveChainDetails: (details) => dispatch(addChainCosmos(details)),
    updateChainDetails: (details) => dispatch(updateChainCosmos(details)),
    clearChainId: () => dispatch(resetCurrentChainId()),
    stepChanger: (step) => dispatch(changeStep(step)),
    pageChanger: (page) => dispatch(changePage(page)),
  };
}

const ChainFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default ChainFormContainer;
