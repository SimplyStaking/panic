import { withFormik } from 'formik';
import { connect } from 'react-redux';
import ChainForm from '../../../components/chains/substrate/forms/chainForm';
import { addChainSubstrate } from '../../../redux/actions/substrateChainsActions';
import ChainSchema from './schemas/chainSchema';

const Form = withFormik({
  mapPropsToErrors: () => ({
    chainName: '',
  }),
  mapPropsToValues: () => ({
    chainName: '',
  }),
  validationSchema: (props) => ChainSchema(props),
  handleSubmit: (values, { props }) => {
    const { saveChainDetails } = props;
    const payload = {
      chainName: values.chainName,
    };
    saveChainDetails(payload);
  },
})(ChainForm);

const mapStateToProps = (state) => ({
  substrateConfigs: state.SubstrateChainsReducer.substrateConfigs,
  config: state.SubstrateChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    saveChainDetails: (details) => dispatch(addChainSubstrate(details)),
  };
}

const ChainFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default ChainFormContainer;
