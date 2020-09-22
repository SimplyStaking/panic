import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { changePage } from '../../redux/actions/pageActions';
import NavigationButton from '../../components/global/navigationButton';

class NavigationButtonContainer extends Component {
  constructor(props) {
    super(props);
    this.nextPage = this.nextPage.bind(this);
  }

  nextPage(page) {
    const { pageChanger } = this.props;
    // Change the upcoming page information
    pageChanger({ page });
  }

  render() {
    const { text, navigation } = this.props;

    return (
      <NavigationButton
        disabled={false}
        nextPage={this.nextPage}
        buttonText={text}
        navigation={navigation}
      />
    );
  }
}

const mapStateToProps = (state) => ({
  page: state.ChangePageReducer.page,
});

function mapDispatchToProps(dispatch) {
  return {
    pageChanger: (page) => dispatch(changePage(page)),
  };
}

NavigationButtonContainer.propTypes = {
  pageChanger: PropTypes.func.isRequired,
  text: PropTypes.string.isRequired,
  navigation: PropTypes.string.isRequired,
};

export default connect(mapStateToProps, mapDispatchToProps)(NavigationButtonContainer);
