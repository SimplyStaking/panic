import { withFormik } from 'formik';
import { connect } from 'react-redux';
import ChainForm from '../../../components/chains/cosmos/forms/chainForm';
import { addChainCosmos } from '../../../redux/actions/cosmosChainsActions';
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
  cosmosConfigs: state.CosmosChainsReducer.cosmosConfigs,
  config: state.CosmosChainsReducer.config,
});

function mapDispatchToProps(dispatch) {
  return {
    saveChainDetails: (details) => dispatch(addChainCosmos(details)),
  };
}

const ChainFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Form);

export default ChainFormContainer;
