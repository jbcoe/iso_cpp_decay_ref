# Specializing decay for reference wrappers

ISO/IEC JTC1 SC22 WG21 Programming Language C++

DXXXX

Working Group: Library Evolution

Date: 2016-11-8

_Jonathan Coe \<jbcoe@me.com\>_

_Walter Brown \<webrown.cpp@gmail.com\>_

## TL;DR

Specialize `std::decay` for `std::reference-wrapper` so that class templates
deduction can handle reference wrappers without explicit deduction guidelines
being provided.

## Introduction
                
Before perfect forwarding, factory functions like `boost::make_shared` took a series of 
`const` references as arguments:

```
template<typename T, typename T1, typename T2>
boost::shared_ptr<T> make_shared(const T1& t1, const T2& t2);
```

To pass a reference to such a function one needed to use
`boost::reference_wrapper` and the helper functions `boost::ref` and
`boost::cref`. `boost::reference_wrapper` is a copyable type that is implicitly
deducable to a reference. 

The introduction of forwarding references into C++11 has rendered the use of
`reference_wrapper` unnecessary when passing references to generic code.
`reference_wrapper` was adopted in C++11 and is needed to pass references to
factory functions for construction of `pair`s and `tuple`s. 

`std::make_pair` and `std::make_tuple` do not use perfect forwarding as that
would too readily result in a tuple of references which is unlikely to be what
a user wanted. Instead they use `std::decay` to strip cv- and
reference-qualifiers from the supplied types and construct a `pair` or `tuple`
of value types. 

If a user wants a `tuple` of references then `make_tuple` must be explictly
passed a refence wrapper. 

```
int x = 0;
double y = 0.0;

auto t1 = std::make_tuple(x, y);
// t1 is std::tuple<int, double>;

auto t2 = std::make_tuple(std::ref(x), y);
// t2 is std::tuple<int&, double>;
```

This design works perfectly but requires special casing of `make_tuple` and
`make_pair` for reference wrappers.


### Template argument deduction for class templates

C++17 introduces template argument deduction for class templates. A user can now write:

```
int x = 0;
double y = 0.0;

auto t = std::tuple(x, y);
// t is std::tuple<int, double>;
```

and the compiler will deduce the type correctly. 

There is discussion about how `reference_wrapper` should interact with template
deduction for class templates and a proposal [REF] has suggested adding
deduction guidelines to explicitly specify the behaviour.

This seems unfortuante as the potential removal of `make_tuple` and similar
factory functions, with their domain specific handling of reference wrappers, is
muddied by having to explictly specify deduction guidelines to recover the
(desirable) interaction with `reference wrapper`.

We propose modifications to `std::decay` so that implicit deduction guidelines
will give 'correct' behaviour for `reference_wrapper`: unwrapping the
reference.

### Specialization of `std::decay` for `std::reference_wrapper`

Reference implementation of `std::decay` with reference implementation.

```
template< class T >
struct decay {
private:
    typedef typename std::remove_reference<T>::type U;
public:
    typedef typename std::conditional< 
        std::is_array<U>::value, 
        typename std::remove_extent<U>::type*, 
        typename std::conditional< 
            std::is_function<U>::value, 
            typename std::add_pointer<U>::type, 
            typename std::remove_cv<U>::type
        >::type
    >::type type;
};

template< class T >
using decay_t = typename decay<T>::type;

// reference_wrapper value
template< class T >
struct decay<std::reference_wrapper<T>> { 
	typedef T& type;
};

template< class T >
struct decay<const std::reference_wrapper<T>> { 
	typedef T& type;
};

// reference_wrapper l-value reference
template< class T >
struct decay<std::reference_wrapper<T>&> { 
	typedef T& type;
};

template< class T >
struct decay<const std::reference_wrapper<T>&> { 
	typedef T& type;
};

// reference_wrapper r-value reference
template< class T >
struct decay<std::reference_wrapper<T>&&> { 
	typedef T& type;
};

template< class T >
struct decay<const std::reference_wrapper<T>&&> { 
	typedef T& type;
};
```

## Impact

Specializing `decay` for `reference_wrapper` makes writing factory functions easy:

```
template <typename ...Ts>
auto make_tuple(Ts&& ...ts) -> std::tuple<std::decay_t<Ts>...>
{
	return std::tuple<std::decay_t<Ts>...>(std::forward<Ts>(ts)...);
} 
```

Compiler-deduced template types can be specified to be deduced using
`std::decay` and users will not need to write code to explicitly handle
reference wrappers.

If a user does want a `tuple` of reference wrappers then it can be explictly
specified:

```
int x = 0;
double y = 0.0;

auto t1 = std::tuple(ref(x), y);
// t1 is std::tuple<int&, double>;

auto t2 = std::tuple<std::reference_wrapper<int>, double>(x, y);
// t2 is std::tuple<std::reference_wrapper<int>, double>;
```

User-defined types can make full use of template deduction and reference
wrappers without any load on the user.  `reference_wrapper` is an
'expert-friendly' feature, this proposal ensures that user-defined class
templates will get its benefits for free.

## Acknowledgements
The authors would like to thank Howard Hinnant for useful discussion.

## References

[TODO]
