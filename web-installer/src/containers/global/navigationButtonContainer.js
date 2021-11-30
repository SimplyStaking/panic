import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { changePage } from 'redux/actions/pageActions';
import NavigationButton from 'components/global/navigationButton';
import PopUp from 'components/global/popUp';

class NavigationButtonContainer extends Component {
  constructor(props) {
    super(props);
    this.nextPage = this.nextPage.bind(this);
    this.handlePopUpResponse = this.handlePopUpResponse.bind(this);
    this.state = {
      popUpActive: false,
      nextPage: '',
    };
  }

  handlePopUpResponse(bool) {
    const { pageChanger } = this.props;
    const { nextPage } = this.state;

    this.controlPopUpActivity(false);
    if (bool) {
      pageChanger({ page: nextPage });
    }
  }

  controlPopUpActivity(bool) {
    this.setState({
      popUpActive: bool,
    });
  }

  nextPage(page) {
    const { pageChanger, dirty } = this.props;

    if (!dirty) {
      // Change the upcoming page information
      pageChanger({ page });
    }

    this.setState({
      nextPage: page,
    });

    this.controlPopUpActivity(true);
  }

  render() {
    const { text, navigation } = this.props;
    const { popUpActive } = this.state;

    return (
      <>
        <NavigationButton
          disabled={false}
          nextPage={this.nextPage}
          buttonText={text}
          navigation={navigation}
        />
        <PopUp
          trigger={popUpActive}
          stepControlAdvanceNextStep={this.handlePopUpResponse}
        />
      </>
    );
  }
}

const mapStateToProps = (state) => ({
  page: state.ChangePageReducer.page,
  dirty: state.ChangePageReducer.dirty,
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
  dirty: PropTypes.bool.isRequired,
};

export default connect(
  mapStateToProps,
  mapDispatchToProps,
)(NavigationButtonContainer);
