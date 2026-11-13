from drafter import *
from dataclasses import dataclass, field


# =====================================================
# DATA CLASSES
# =====================================================

@dataclass
class Assignment:
    name: str
    earned_points: float
    possible_points: float
    category: str


@dataclass
class GradeCategory:
    name: str
    weight: float
    drop_lowest: bool = False
    remaining_points: float = 0.0
    expected_score: float = 90.0


@dataclass
class Course:
    name: str
    categories: list[GradeCategory] = field(default_factory=list)
    assignments: list[Assignment] = field(default_factory=list)


@dataclass
class State:
    courses: list[Course] = field(default_factory=list)
    selected_course: int = 0
    target_grade: float = 85.0
    current_grade: float = 0.0
    page: str = "home"


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def get_selected_course(state: State) -> Course:
    return state.courses[state.selected_course]


def category_weight_total(course: Course) -> float:
    total = 0.0

    for category in course.categories:
        total += category.weight

    return total


def get_counted_points(course: Course,
                       category: GradeCategory) -> tuple[float, float]:
    matching = []

    for assignment in course.assignments:
        if assignment.category == category.name:
            matching.append(assignment)

    # Drop one lowest percentage grade when enabled.
    # Only drop if at least two assignments are present.
    if category.drop_lowest and len(matching) >= 2:
        lowest = matching[0]

        for assignment in matching:
            assignment_percent = (
                assignment.earned_points / assignment.possible_points
            )

            lowest_percent = (
                lowest.earned_points / lowest.possible_points
            )

            if assignment_percent < lowest_percent:
                lowest = assignment

        matching.remove(lowest)

    earned = 0.0
    possible = 0.0

    for assignment in matching:
        earned += assignment.earned_points
        possible += assignment.possible_points

    return earned, possible


def calculate_category_average(course: Course,
                               category: GradeCategory):
    earned, possible = get_counted_points(course, category)

    if possible == 0:
        return None

    return earned / possible * 100


def calculate_current_grade(course: Course):
    weighted_total = 0.0
    active_weight = 0.0

    for category in course.categories:
        average = calculate_category_average(course, category)

        if average is not None and category.weight > 0:
            weighted_total += average * category.weight
            active_weight += category.weight

    if active_weight == 0:
        return None

    # Current grade is normalized across categories
    # that already contain graded assignments.
    return weighted_total / active_weight


def category_choices(course: Course) -> list[str]:
    choices = []

    for i in range(len(course.categories)):
        choices.append(
            str(i) + ": " + course.categories[i].name
        )

    return choices


def read_category_index(choice: str) -> int:
    return int(choice.split(":")[0])


def weights_are_valid(course: Course) -> bool:
    return abs(category_weight_total(course) - 100.0) < 0.001


# =====================================================
# HOME PAGE
# =====================================================

@route
def index(state: State) -> Page:
    content = [
        Header("Grade Goal Calculator"),
        "Track your grades and plan the scores you need.",
        Button("Add a Course", "new_course_page")
    ]

    if len(state.courses) == 0:
        content.append("You have not added any courses yet.")

    else:
        course_names = []

        for course in state.courses:
            course_names.append(course.name)

        content.extend([
            Header("Your Courses", 2),
            "Select a course:",
            SelectBox(
                "course_choice",
                course_names,
                course_names[state.selected_course]
            ),
            Button("Open Course", "select_course")
        ])

    content.extend([
        Button("Reset All Data", "reset_data")
    ])

    return Page(state, content)


@route
def reset_data(state: State) -> Page:
    state.courses = []
    state.selected_course = 0
    state.target_grade = 85.0
    state.current_grade = 0.0
    state.page = "home"

    return index(state)



# =====================================================
# COURSE MANAGEMENT
# =====================================================

@route
def new_course_page(state: State) -> Page:
    return Page(state, [
        Header("Add a New Course"),
        "Course name:",
        TextBox("course_name"),
        Button("Save Course", "add_course"),
        Button("Back Home", "index")
    ])


@route
def add_course(state: State, course_name: str) -> Page:
    course_name = course_name.strip()

    if course_name == "":
        return Page(state, [
            "Course name cannot be empty.",
            Button("Try Again", "new_course_page")
        ])

    state.courses.append(Course(course_name))
    state.selected_course = len(state.courses) - 1

    return course_dashboard(state)


@route
def select_course(state: State, course_choice: str) -> Page:
    for i in range(len(state.courses)):
        if state.courses[i].name == course_choice:
            state.selected_course = i
            break

    return course_dashboard(state)
@route
def edit_course_name_page(state: State) -> Page:
    course = get_selected_course(state)

    return Page(state, [
        Header("Edit Course Name"),
        "Enter the new course name:",
        TextBox("new_course_name", course.name),
        Button("Save Changes", "update_course_name"),
        Button("Cancel", "course_dashboard")
    ])
@route
def update_course_name(state: State,
                       new_course_name: str) -> Page:
    course = get_selected_course(state)

    new_course_name = new_course_name.strip()

    if new_course_name == "":
        return Page(state, [
            Header("Invalid Course Name"),
            "Course name cannot be empty.",
            Button("Try Again", "edit_course_name_page")
        ])

    for i in range(len(state.courses)):
        if i != state.selected_course:
            if state.courses[i].name.lower() == new_course_name.lower():
                return Page(state, [
                    Header("Course Already Exists"),
                    "You already have a course with this name.",
                    Button("Try Again", "edit_course_name_page")
                ])

    course.name = new_course_name

    return course_dashboard(state)


# =====================================================
# COURSE DASHBOARD
# =====================================================

@route
def course_dashboard(state: State) -> Page:
    course = get_selected_course(state)
    current = calculate_current_grade(course)

    content = [
    Header(course.name),
    Button("Edit Course Name", "edit_course_name_page"),
    Header("Current Grade", 2)
 ]

    if current is None:
        content.append("No grades have been entered yet.")
    else:
        state.current_grade = current
        content.append(str(round(current, 2)) + "%")

    content.extend([
        "Grading weights total: "
        + str(round(category_weight_total(course), 2)) + "%",
        Button("Manage Categories", "categories_page"),
        Button("Add Assignment", "add_assignment_page"),
        Button("View Assignments", "assignments_page"),
        Button("Grade Goal Calculator", "calculator_page"),
        Button("Back Home", "index")
    ])

    return Page(state, content)


# =====================================================
# CATEGORY MANAGEMENT
# =====================================================

@route
def categories_page(state: State) -> Page:
    course = get_selected_course(state)

    content = [
        Header("Grading Categories"),
        Header(course.name, 2)
    ]

    if len(course.categories) == 0:
        content.append("No grading categories added yet.")

    for category in course.categories:
        content.append(Header(category.name, 3))
        content.append(
            "Weight: " + str(category.weight) + "%"
        )

        if category.drop_lowest:
            content.append("Lowest assignment: Dropped")
        else:
            content.append("Lowest assignment: Not dropped")

        average = calculate_category_average(course, category)

        if average is None:
            content.append("Current category grade: No grades")
        else:
            content.append(
                "Current category grade: "
                + str(round(average, 2)) + "%"
            )

    content.extend([
        "Total weight: "
        + str(round(category_weight_total(course), 2)) + "%",
        Button("Add Category", "add_category_page"),
        Button("Edit Category Name", "edit_category_name_page"),
        Button("Edit Category Weight", "edit_weight_page"),
        Button("Back to Course", "course_dashboard")
        
    ])

    return Page(state, content)


@route
def add_category_page(state: State) -> Page:
    return Page(state, [
        Header("Add Grading Category"),
        "Category name (Exams, Homework, Quizzes, etc.):",
        TextBox("category_name"),
        "Category weight (%):",
        TextBox("category_weight", 0, kind="number"),
        CheckBox("drop_lowest"),
        " Drop the lowest assignment in this category",
        Button("Save Category", "add_category"),
        Button("Back", "categories_page")
    ])


@route
def add_category(state: State,
                 category_name: str,
                 category_weight: float,
                 drop_lowest: bool) -> Page:
    course = get_selected_course(state)
    category_name = category_name.strip()

    if category_name == "":
        return Page(state, [
            "Category name cannot be empty.",
            Button("Try Again", "add_category_page")
        ])

    if category_weight <= 0 or category_weight > 100:
        return Page(state, [
            "Weight must be greater than 0 and at most 100.",
            Button("Try Again", "add_category_page")
        ])

    for category in course.categories:
        if category.name.lower() == category_name.lower():
            return Page(state, [
                "That category already exists.",
                Button("Try Again", "add_category_page")
            ])

    new_total = (
        category_weight_total(course) + category_weight
    )

    if new_total > 100.001:
        return Page(state, [
            "Adding this category would exceed 100%.",
            Button("Try Again", "add_category_page")
        ])

    course.categories.append(
        GradeCategory(
            category_name,
            category_weight,
            drop_lowest
        )
    )

    return categories_page(state)

@route
def edit_category_name_page(state: State) -> Page:
    course = get_selected_course(state)

    if len(course.categories) == 0:
        return Page(state, [
            Header("No Categories"),
            "Add a category before editing its name.",
            Button("Back", "categories_page")
        ])

    return Page(state, [
        Header("Edit Category Name"),
        "Choose the category:",
        SelectBox(
            "category_choice",
            category_choices(course)
        ),
        "Enter the new category name:",
        TextBox("new_category_name"),
        Button("Save Changes", "update_category_name"),
        Button("Cancel", "categories_page")
    ])

@route
def update_category_name(state: State,
                         category_choice: str,
                         new_category_name: str) -> Page:

    course = get_selected_course(state)
    new_category_name = new_category_name.strip()

    if new_category_name == "":
        return Page(state, [
            Header("Invalid Category Name"),
            "Category name cannot be empty.",
            Button("Try Again", "edit_category_name_page")
        ])

    category_index = read_category_index(category_choice)
    category = course.categories[category_index]

    # Prevent duplicate category names.
    for i in range(len(course.categories)):
        if i != category_index:
            if course.categories[i].name.lower() == new_category_name.lower():
                return Page(state, [
                    Header("Category Already Exists"),
                    "A category with that name already exists.",
                    Button("Try Again", "edit_category_name_page")
                ])

    old_name = category.name

    # Update the category name.
    category.name = new_category_name

    # Update assignments belonging to this category.
    for assignment in course.assignments:
        if assignment.category == old_name:
            assignment.category = new_category_name

    return categories_page(state)



@route
def edit_weight_page(state: State) -> Page:
    course = get_selected_course(state)

    if len(course.categories) == 0:
        return Page(state, [
            "Add a category first.",
            Button("Back", "categories_page")
        ])

    return Page(state, [
        Header("Edit Category Weight"),
        "Choose category:",
        SelectBox(
            "category_choice",
            category_choices(course)
        ),
        "New weight (%):",
        TextBox("new_weight", 20, kind="number"),
        Button("Update Weight", "update_weight"),
        Button("Back", "categories_page")
    ])


@route
def update_weight(state: State,
                  category_choice: str,
                  new_weight: float) -> Page:
    course = get_selected_course(state)

    if new_weight <= 0 or new_weight > 100:
        return Page(state, [
            "Weight must be between 0 and 100.",
            Button("Try Again", "edit_weight_page")
        ])

    index_number = read_category_index(category_choice)
    category = course.categories[index_number]

    new_total = (
        category_weight_total(course)
        - category.weight
        + new_weight
    )

    if new_total > 100.001:
        return Page(state, [
            "Total category weights cannot exceed 100%.",
            Button("Try Again", "edit_weight_page")
        ])

    category.weight = new_weight

    return categories_page(state)


# =====================================================
# ASSIGNMENT MANAGEMENT
# =====================================================

@route
def add_assignment_page(state: State) -> Page:
    course = get_selected_course(state)

    if len(course.categories) == 0:
        return Page(state, [
            Header("No Categories"),
            "Add a grading category before adding assignments.",
            Button("Add Category", "add_category_page"),
            Button("Back", "course_dashboard")
        ])

    return Page(state, [
        Header("Add Assignment"),
        "Assignment name:",
        TextBox("assignment_name"),
        "Assignment category:",
        SelectBox(
            "category_choice",
            category_choices(course)
        ),
        "Points earned:",
        TextBox("earned_points", 0, kind="number"),
        "Total possible points:",
        TextBox("possible_points", 100, kind="number"),
        Button("Save Assignment", "save_assignment"),
        Button("Back", "course_dashboard")
    ])


@route
def save_assignment(state: State,
                    assignment_name: str,
                    category_choice: str,
                    earned_points: float,
                    possible_points: float) -> Page:
    course = get_selected_course(state)
    assignment_name = assignment_name.strip()

    if assignment_name == "":
        return Page(state, [
            "Assignment name cannot be empty.",
            Button("Try Again", "add_assignment_page")
        ])

    if possible_points <= 0:
        return Page(state, [
            "Possible points must be greater than zero.",
            Button("Try Again", "add_assignment_page")
        ])

    if earned_points < 0 or earned_points > possible_points:
        return Page(state, [
            "Earned points must be between 0 and possible points.",
            Button("Try Again", "add_assignment_page")
        ])

    category_index = read_category_index(category_choice)
    category_name = course.categories[category_index].name

    course.assignments.append(
        Assignment(
            assignment_name,
            earned_points,
            possible_points,
            category_name
        )
    )

    return assignments_page(state)


@route
def assignments_page(state: State) -> Page:
    course = get_selected_course(state)

    content = [
        Header("Assignments"),
        Header(course.name, 2)
    ]

    if len(course.assignments) == 0:
        content.append("No assignments have been added.")

    for assignment in course.assignments:
        percent = (
            assignment.earned_points
            / assignment.possible_points
        ) * 100

        content.append(Header(assignment.name, 3))
        content.append("Category: " + assignment.category)
        content.append(
            "Score: "
            + str(assignment.earned_points)
            + " / "
            + str(assignment.possible_points)
            + " ("
            + str(round(percent, 2))
            + "%)"
        )

    content.extend([
        Button("Add Another Assignment", "add_assignment_page"),
        Button("Back to Course", "course_dashboard")
    ])

    return Page(state, content)


# =====================================================
# GRADE CALCULATOR MENU
# =====================================================

@route
def calculator_page(state: State) -> Page:
    course = get_selected_course(state)

    content = [
        Header("Grade Goal Calculator"),
        Header(course.name, 2),
        "Set the remaining points in each category "
        "before calculating your grade goals."
    ]

    for category in course.categories:
        content.append(Header(category.name, 3))
        content.append(
            "Weight: " + str(category.weight) + "%"
        )
        content.append(
            "Points remaining: "
            + str(category.remaining_points)
        )
        content.append(
            "Expected future score: "
            + str(category.expected_score) + "%"
        )

    content.extend([
        Button("Set Remaining Points", "remaining_points_page"),
        Button("Set Expected Scores", "expected_scores_page"),
        Button("Calculate Same Score Across All Categories",
               "target_grade_page"),
        Button("Calculate Score for One Assignment Type",
               "specific_grade_page"),
        Button("Back to Course", "course_dashboard")
    ])

    return Page(state, content)


# =====================================================
# REMAINING ASSIGNMENT POINTS
# =====================================================

@route
def remaining_points_page(state: State) -> Page:
    course = get_selected_course(state)

    if len(course.categories) == 0:
        return Page(state, [
            "Add categories first.",
            Button("Back", "calculator_page")
        ])

    return Page(state, [
        Header("Plan Remaining Work"),
        "Choose an assignment type:",
        SelectBox(
            "category_choice",
            category_choices(course)
        ),
        "Total possible points remaining in this category:",
        TextBox("remaining_points", 0, kind="number"),
        Button("Save Remaining Points", "save_remaining_points"),
        Button("Back", "calculator_page")
    ])


@route
def save_remaining_points(state: State,
                          category_choice: str,
                          remaining_points: float) -> Page:
    if remaining_points < 0:
        return Page(state, [
            "Remaining points cannot be negative.",
            Button("Try Again", "remaining_points_page")
        ])

    course = get_selected_course(state)
    category_index = read_category_index(category_choice)

    course.categories[category_index].remaining_points = (
        remaining_points
    )

    return calculator_page(state)


# =====================================================
# EXPECTED FUTURE SCORES
# =====================================================

@route
def expected_scores_page(state: State) -> Page:
    course = get_selected_course(state)

    content = [
        Header("Expected Future Scores"),
        "These are the scores you think you will earn "
        "on remaining assignments."
    ]

    for category in course.categories:
        content.append(
            category.name + ": "
            + str(category.expected_score) + "%"
        )

    content.extend([
        Button("Edit Expected Score", "edit_expected_score_page"),
        Button("Back to Calculator", "calculator_page")
    ])

    return Page(state, content)


@route
def edit_expected_score_page(state: State) -> Page:
    course = get_selected_course(state)

    if len(course.categories) == 0:
        return Page(state, [
            "Add a category first.",
            Button("Back", "calculator_page")
        ])

    return Page(state, [
        Header("Edit Expected Score"),
        "Select an assignment type:",
        SelectBox(
            "category_choice",
            category_choices(course)
        ),
        "Expected percentage on remaining assignments:",
        TextBox("expected_score", 90, kind="number"),
        Button("Save Expected Score", "save_expected_score"),
        Button("Back", "expected_scores_page")
    ])


@route
def save_expected_score(state: State,
                        category_choice: str,
                        expected_score: float) -> Page:
    if expected_score < 0 or expected_score > 100:
        return Page(state, [
            "Expected score must be between 0 and 100.",
            Button("Try Again", "edit_expected_score_page")
        ])

    course = get_selected_course(state)
    category_index = read_category_index(category_choice)

    course.categories[category_index].expected_score = (
        expected_score
    )

    return expected_scores_page(state)


# =====================================================
# CALCULATOR 1:
# SAME SCORE ON ALL REMAINING WORK
# =====================================================

@route
def target_grade_page(state: State) -> Page:
    return Page(state, [
        Header("Calculate Needed Average"),
        "What final course grade do you want?",
        TextBox(
            "target_grade",
            state.target_grade,
            kind="number"
        ),
        Button("Calculate Required Average",
               "calculate_required_grade"),
        Button("Back", "calculator_page")
    ])


@route
def calculate_required_grade(state: State,
                             target_grade: float) -> Page:
    course = get_selected_course(state)

    if target_grade < 0 or target_grade > 100:
        return Page(state, [
            "Target grade must be between 0 and 100.",
            Button("Try Again", "target_grade_page")
        ])

    if not weights_are_valid(course):
        return Page(state, [
            "Category weights must total exactly 100%.",
            Button("Edit Categories", "categories_page")
        ])

    state.target_grade = target_grade

    # Projected final grade:
    # fixed_contribution + remaining_fraction * future_score
    fixed_contribution = 0.0
    remaining_fraction = 0.0

    for category in course.categories:
        earned, possible = get_counted_points(
            course, category
        )

        total_possible = (
            possible + category.remaining_points
        )

        if total_possible <= 0:
            return Page(state, [
                "Missing grade information for " + category.name,
                "Add an assignment or enter remaining points.",
                Button("Set Remaining Points",
                       "remaining_points_page")
            ])

        weight_fraction = category.weight / 100

        fixed_contribution += (
            weight_fraction * earned / total_possible
        )

        remaining_fraction += (
            weight_fraction
            * category.remaining_points
            / total_possible
        )

    if remaining_fraction == 0:
        final_grade = fixed_contribution * 100

        return Page(state, [
            Header("Grade Goal Results"),
            "No remaining assignment points were entered.",
            "Calculated final grade: "
            + str(round(final_grade, 2)) + "%",
            Button("Back", "calculator_page")
        ])

    needed_fraction = (
        target_grade / 100 - fixed_contribution
    ) / remaining_fraction

    needed_percent = needed_fraction * 100

    content = [
        Header("Grade Goal Results"),
        "Target final grade: "
        + str(round(target_grade, 2)) + "%"
    ]

    if needed_percent > 100:
        content.append(
            "Your target is not achievable with scores "
            "of 100% or less on remaining work."
        )
        content.append(
            "Required average would be "
            + str(round(needed_percent, 2)) + "%."
        )

    elif needed_percent <= 0:
        content.append(
            "You can reach your target even with 0% "
            "on the remaining work."
        )

    else:
        content.append(
            "Needed average on all remaining work: "
            + str(round(needed_percent, 2)) + "%"
        )

    content.append(Header("Assignment Type Goals", 2))

    for category in course.categories:
        if category.remaining_points > 0:
            content.append(Header(category.name, 3))

            if 0 < needed_percent <= 100:
                needed_points = (
                    category.remaining_points
                    * needed_fraction
                )

                content.append(
                    "Needed percentage: "
                    + str(round(needed_percent, 2)) + "%"
                )

                content.append(
                    "Needed points: "
                    + str(round(needed_points, 2))
                    + " / "
                    + str(category.remaining_points)
                )
            else:
                content.append(
                    "Remaining possible points: "
                    + str(category.remaining_points)
                )

    content.extend([
        "This calculation assumes the same percentage "
        "on all remaining assignment types.",
        Button("Try Another Target", "target_grade_page"),
        Button("Back to Calculator", "calculator_page")
    ])

    return Page(state, content)


# =====================================================
# CALCULATOR 2:
# SOLVE FOR ONE ASSIGNMENT TYPE
# =====================================================

@route
def specific_grade_page(state: State) -> Page:
    course = get_selected_course(state)

    choices = []

    for i in range(len(course.categories)):
        category = course.categories[i]

        if category.remaining_points > 0:
            choices.append(
                str(i) + ": " + category.name
            )

    if len(choices) == 0:
        return Page(state, [
            Header("No Remaining Work"),
            "Enter remaining points for at least one category.",
            Button("Set Remaining Points", "remaining_points_page")
        ])

    return Page(state, [
        Header("Calculate a Specific Grade"),
        "Target final course grade:",
        TextBox(
            "target_grade",
            state.target_grade,
            kind="number"
        ),
        "Which assignment type should we solve for?",
        SelectBox("category_choice", choices),
        Button("Calculate Needed Score",
               "calculate_specific_grade"),
        Button("Edit Expected Scores", "expected_scores_page"),
        Button("Back", "calculator_page")
    ])


@route
def calculate_specific_grade(state: State,
                             target_grade: float,
                             category_choice: str) -> Page:
    course = get_selected_course(state)

    if target_grade < 0 or target_grade > 100:
        return Page(state, [
            "Target grade must be between 0 and 100.",
            Button("Try Again", "specific_grade_page")
        ])

    if not weights_are_valid(course):
        return Page(state, [
            "Category weights must total 100%.",
            Button("Edit Categories", "categories_page")
        ])

    state.target_grade = target_grade

    selected_index = read_category_index(category_choice)
    selected_category = course.categories[selected_index]

    if selected_category.remaining_points <= 0:
        return Page(state, [
            "The selected category has no remaining points.",
            Button("Back", "specific_grade_page")
        ])

    # Calculate contributions from all OTHER categories.
    other_contributions = 0.0

    for i in range(len(course.categories)):
        if i != selected_index:
            category = course.categories[i]

            earned, possible = get_counted_points(
                course, category
            )

            remaining = category.remaining_points
            final_possible = possible + remaining

            if final_possible <= 0:
                return Page(state, [
                    "Missing information for " + category.name,
                    "Add an assignment or enter remaining points.",
                    Button("Set Remaining Points",
                           "remaining_points_page")
                ])

            expected_points = (
                remaining * category.expected_score / 100
            )

            projected_category_grade = (
                (earned + expected_points)
                / final_possible
            ) * 100

            other_contributions += (
                projected_category_grade
                * category.weight / 100
            )

    # Solve for the selected category.
    earned, possible = get_counted_points(
        course, selected_category
    )

    remaining = selected_category.remaining_points
    final_possible = possible + remaining
    weight_fraction = selected_category.weight / 100

    required_category_grade = (
        target_grade - other_contributions
    ) / weight_fraction

    required_future_points = (
        required_category_grade / 100
    ) * final_possible - earned

    required_percent = (
        required_future_points / remaining
    ) * 100

    content = [
        Header("Grade Goal Results"),
        "Target final grade: "
        + str(round(target_grade, 2)) + "%",
        Header(selected_category.name, 2)
    ]

    if required_percent > 100:
        content.append(
            "Your target is not achievable with the "
            "expected scores entered for other categories."
        )
        content.append(
            "Required percentage: "
            + str(round(required_percent, 2)) + "%"
        )

    elif required_percent <= 0:
        content.append(
            "You can reach your target even with 0% "
            "on the remaining work in this category."
        )

    else:
        content.append(
            "You need an average of "
            + str(round(required_percent, 2))
            + "% on your remaining "
            + selected_category.name.lower() + "."
        )

        content.append(
            "Equivalent points needed: "
            + str(round(required_future_points, 2))
            + " / "
            + str(remaining)
        )

    content.append(
        Header("Expected Scores in Other Categories", 2)
    )

    for i in range(len(course.categories)):
        if i != selected_index:
            category = course.categories[i]

            if category.remaining_points > 0:
                content.append(
                    category.name + ": "
                    + str(category.expected_score)
                    + "%"
                )

    content.extend([
        "Results assume the expected scores shown above "
        "on remaining work in the other categories.",
        Button("Try Another Category", "specific_grade_page"),
        Button("Change Expected Scores", "expected_scores_page"),
        Button("Back to Calculator", "calculator_page")
    ])

    return Page(state, content)



# =====================================================
# WEBSITE DESIGN
# =====================================================

set_website_style("none")

add_website_css("""
#drafter-body-- {
    max-width: 650px;
    margin: 20px auto;
    padding: 12px;
    background-color: #eeeeee;
    border: 1px solid #aaaaaa;
    border-radius: 6px;
    font-family: Arial, sans-serif;
    color: #111111;
    box-sizing: border-box;
}

#drafter-body-- h1 {
    background-color: #142D4E;
    color: white;
    text-align: center;
    font-size: 22px;
    padding: 10px;
    margin: 0 0 18px 0;
    border-radius: 5px;
}

#drafter-body-- h2 {
    color: #142D4E;
    border-bottom: 1px solid #cccccc;
    padding-bottom: 6px;
    margin-top: 20px;
}

#drafter-body-- button:hover {
    background-color: #DCE5EF;
}


}

#drafter-body-- h3 {
    color: #333333;
    margin-top: 16px;
}

#drafter-body-- button {
    background-color: #f5f5f5;
    color: #111111;
    border: 1px solid #999999;
    border-radius: 5px;
    padding: 9px 18px;
    font-size: 15px;
    margin: 6px 4px;
    cursor: pointer;
}

#drafter-body-- button:hover {
    background-color: #dddddd;
}

#drafter-body-- input,
#drafter-body-- select {
    background-color: white;
    color: #111111;
    border: 1px solid #cccccc;
    border-radius: 2px;
    padding: 7px;
    font-size: 15px;
    max-width: 100%;
    box-sizing: border-box;
}

#drafter-body-- p {
    line-height: 1.5;
}

#drafter-body-- hr {
    border: none;
    border-top: 1px solid #cccccc;
    margin: 18px 0;
}

@media (max-width: 600px) {
    #drafter-body-- {
        margin: 5px;
        padding: 9px;
    }

    #drafter-body-- input,
    #drafter-body-- select {
        max-width: 100%;
    }
}
""")



# =====================================================
# START APPLICATION
# =====================================================

start_server(State())



