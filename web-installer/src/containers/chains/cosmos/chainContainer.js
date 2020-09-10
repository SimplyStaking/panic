import { withFormik } from 'formik';
import { connect } from 'react-redux';
import ChainForm from '../../../components/chains/cosmos/forms/chainForm';
import { addChain } from '../../../redux/actions/chainsActions';
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
  cosmosConfigs: state.ChainsReducer.cosmosConfigs,
});

function mapDispatchToProps(dispatch) {
  return {
    saveChainDetails: (details) => dispatch(addChain(details)),
  };
}

const ChainFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default ChainFormContainer;
