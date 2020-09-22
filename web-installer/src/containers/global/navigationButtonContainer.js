import React, { Component } from 'react'
import { connect } from "react-redux";

import { changePage } from "../../redux/actions/pageActions";
import NavigationButton from "../../components/global/navigationButton";

class NavigationButtonContainer extends Component {

    constructor(props) {
        super(props);
        this.nextPage = this.nextPage.bind(this);
    }

    nextPage( page ){
        // Change the upcoming page information
        this.props.changePage({ page });
    }

    render() {
        return (
            <NavigationButton 
                nextPage={this.nextPage}
                buttonText={this.props.text}
                navigation={this.props.navigation}
            />
        )
    }
}

const mapStateToProps = state => {
    return { 
        page: state.ChangePageReducer.page,
    };
};

function mapDispatchToProps(dispatch) {
    return {
        changePage: page => dispatch(changePage(page))
    }
}

export default connect(mapStateToProps, mapDispatchToProps)(NavigationButtonContainer);