import { withFormik } from 'formik';
import { connect } from 'react-redux';
import ChainForm from '../../../components/chains/substrate/forms/chainForm';
import { addChainSubstrate, updateChainSubstrate, resetCurrentChainId } from '../../../redux/actions/substrateActions';
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
  config: state.SubstrateChainsReducer,
  currentChain: state.CurrentSubstrateChain,
});

// step and page changers are used diretly in this form instead of their
// respective button containers as extra functionality is needed for the
// onSubmit events.
function mapDispatchToProps(dispatch) {
  return {
    saveChainDetails: (details) => dispatch(addChainSubstrate(details)),
    updateChainDetails: (details) => dispatch(updateChainSubstrate(details)),
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
